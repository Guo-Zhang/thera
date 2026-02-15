"""
飞书知识库 API 客户端

核心功能:
- 认证管理: 使用 SDK 自动管理 tenant_access_token
- 知识空间节点查询: 获取知识空间下的节点列表和详细信息
- 文档到 JupyterBook 转换: 将飞书文档转换为 Markdown 格式

依赖:
- lark-oapi: 飞书开放平台官方 Python SDK
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


def create_lark_client() -> Any:
    """创建飞书 API 客户端"""
    from lark_oapi import Client

    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")

    return (
        Client.builder()
        .app_id(app_id)
        .app_secret(app_secret)
        .log_level(1)  # INFO
        .build()
    )


def style_to_dict(style) -> dict:
    """将 style 对象转换为可序列化的字典"""
    if style is None:
        return None
    return {
        "bold": getattr(style, "bold", False),
        "italic": getattr(style, "italic", False),
        "strikethrough": getattr(style, "strikethrough", False),
        "underline": getattr(style, "underline", False),
        "inline_code": getattr(style, "inline_code", False),
        "link": getattr(style, "link", None),
    }


def apply_style(content: str, style: Dict[str, Any]) -> str:
    """应用文本样式"""
    if not content:
        return ""

    result = content

    if style.get("bold"):
        result = f"**{result}**"
    if style.get("italic"):
        result = f"*{result}*"
    if style.get("strikethrough"):
        result = f"~~{result}~~"
    if style.get("underline"):
        result = f"<u>{result}</u>"
    if style.get("inline_code"):
        result = f"`{result}`"
    if style.get("link"):
        result = f"[{result}]({style['link']})"

    return result


def block_to_dict(block) -> dict:
    """将 block 对象转换为字典"""
    data = {
        "block_id": block.block_id,
        "block_type": block.block_type,
        "parent_id": getattr(block, "parent_id", None),
        "children": getattr(block, "children", None),
    }

    if block.text is not None:
        data["text"] = {
            "style": style_to_dict(getattr(block.text, "style", None)),
            "elements": [],
        }
        if hasattr(block.text, "elements") and block.text.elements:
            for elem in block.text.elements:
                elem_data = {"type": getattr(elem, "type", None)}
                if hasattr(elem, "text_run"):
                    elem_data["text_run"] = {
                        "content": getattr(elem.text_run, "content", None),
                        "style": style_to_dict(getattr(elem.text_run, "style", None)),
                    }
                data["text"]["elements"].append(elem_data)

    return data


def list_space_nodes(
    client: Any, space_id: str, parent_node_token: Optional[str] = None
):
    """获取知识空间子节点列表"""
    from lark_oapi.api.wiki.v2 import ListSpaceNodeRequest

    request = ListSpaceNodeRequest.builder().space_id(space_id).page_size(50)

    if parent_node_token:
        request.parent_node_token(parent_node_token)

    response = client.wiki.v2.space_node.list(request.build())

    if not response.success():
        raise Exception(f"failed to get space nodes: {response.code} {response.msg}")

    return response.data


def build_directory_tree(
    client: Any,
    space_id: str,
    parent_node_token: Optional[str] = None,
    save_docs: bool = True,
) -> List[Dict[str, Any]]:
    """递归构建知识库目录树结构"""
    nodes = []
    page_token = None

    while True:
        result = list_space_nodes(client, space_id, parent_node_token, page_token)

        if result and result.items:
            for item in result.items:
                node_info = {
                    "node_token": item.node_token,
                    "obj_token": item.obj_token,
                    "obj_type": item.obj_type,
                    "title": item.title,
                    "has_child": item.has_child or False,
                    "node_create_time": item.node_create_time,
                    "children": [],
                }

                if save_docs and item.obj_type == "docx" and item.obj_token:
                    save_document_content(item.obj_token, item.title, client)

                if item.has_child:
                    node_info["children"] = build_directory_tree(
                        client, space_id, item.node_token, save_docs
                    )

                nodes.append(node_info)

        if result.has_more and result.page_token:
            page_token = result.page_token
        else:
            break

    return nodes


def save_document_content(obj_token: str, title: str, client: Any) -> None:
    """获取并保存文档内容"""
    from lark_oapi.api.docx.v1 import ListDocumentBlockRequest

    page_token = None
    block_dict = {}

    while True:
        request = (
            ListDocumentBlockRequest.builder().document_id(obj_token).page_size(100)
        )

        if page_token:
            request.page_token(page_token)

        response = client.docx.v1.document_block.list(request.build())

        if not response.success():
            return

        if response.data and response.data.items:
            for block in response.data.items:
                block_dict[block.block_id] = block_to_dict(block)

        if response.data.has_more and response.data.page_token:
            page_token = response.data.page_token
        else:
            break

    doc_data = {
        "title": title,
        "obj_token": obj_token,
        "blocks": list(block_dict.values()),
    }

    safe_title = "".join(
        c for c in title if c.isalnum() or c in (" ", "-", "_")
    ).strip()
    if not safe_title:
        safe_title = f"doc_{obj_token}"

    print(f"  Saved: {title} ({len(block_dict)} blocks)")


# === JupyterBook Converter ===


def block_type_to_markdown(block: Dict[str, Any]) -> str:
    """将飞书 block 转换为 Markdown"""
    block_type = block.get("block_type", 0)
    result = ""

    if block_type == 2:
        result += _text_block_to_markdown(block)
    elif block_type == 3:
        result += _heading_block_to_markdown(block, 1)
    elif block_type == 4:
        result += _heading_block_to_markdown(block, 2)
    elif block_type == 5:
        result += _heading_block_to_markdown(block, 3)
    elif block_type == 6:
        result += _heading_block_to_markdown(block, 4)
    elif block_type == 7:
        result += _heading_block_to_markdown(block, 5)
    elif block_type == 8:
        result += _heading_block_to_markdown(block, 6)
    elif block_type == 12:
        result += _bullet_block_to_markdown(block)
    elif block_type == 13:
        result += _ordered_block_to_markdown(block)
    elif block_type == 14:
        result += _quote_block_to_markdown(block)
    elif block_type == 15:
        result += "\n---\n"

    return result


def _text_block_to_markdown(block: Dict[str, Any]) -> str:
    elements = block.get("text", {}).get("elements", [])
    if not elements:
        return ""

    text_parts = []
    for elem in elements:
        if elem and "text_run" in elem and elem["text_run"]:
            content = elem["text_run"].get("content", "")
            style = elem["text_run"].get("style") or {}
            text_parts.append(apply_style(content, style))

    result = "".join(text_parts).strip()
    return f"{result}\n\n" if result else ""


def _heading_block_to_markdown(block: Dict[str, Any], level: int) -> str:
    elements = block.get("text", {}).get("elements", [])
    if not elements:
        return ""

    text_parts = []
    for elem in elements:
        if elem and "text_run" in elem and elem["text_run"]:
            content = elem["text_run"].get("content", "")
            style = elem["text_run"].get("style") or {}
            text_parts.append(apply_style(content, style))

    title = "".join(text_parts).strip()
    return f"{'#' * level} {title}\n\n" if title else ""


def _bullet_block_to_markdown(block: Dict[str, Any]) -> str:
    elements = block.get("text", {}).get("elements", [])
    if not elements:
        return ""

    text_parts = []
    for elem in elements:
        if elem and "text_run" in elem and elem["text_run"]:
            content = elem["text_run"].get("content", "")
            style = elem["text_run"].get("style") or {}
            text_parts.append(apply_style(content, style))

    text = "".join(text_parts).strip()
    return f"- {text}\n" if text else ""


def _ordered_block_to_markdown(block: Dict[str, Any]) -> str:
    elements = block.get("text", {}).get("elements", [])
    if not elements:
        return ""

    text_parts = []
    for elem in elements:
        if elem and "text_run" in elem and elem["text_run"]:
            content = elem["text_run"].get("content", "")
            style = elem["text_run"].get("style") or {}
            text_parts.append(apply_style(content, style))

    text = "".join(text_parts).strip()
    return f"1. {text}\n" if text else ""


def _quote_block_to_markdown(block: Dict[str, Any]) -> str:
    elements = block.get("text", {}).get("elements", [])
    if not elements:
        return ""

    text_parts = []
    for elem in elements:
        if elem and "text_run" in elem and elem["text_run"]:
            content = elem["text_run"].get("content", "")
            style = elem["text_run"].get("style") or {}
            text_parts.append(apply_style(content, style))

    text = "".join(text_parts).strip()
    return f"> {text}\n" if text else ""


def convert_document_to_markdown(doc_file: Path) -> str:
    """将飞书文档 JSON 转换为 Markdown"""
    with open(doc_file, encoding="utf-8") as f:
        doc_data = json.load(f)

    title = doc_data.get("title", "Untitled")
    blocks = doc_data.get("blocks", [])

    markdown = f"# {title}\n\n"

    for block in blocks:
        markdown += block_type_to_markdown(block)

    return markdown


def get_safe_filename(title: str) -> str:
    """生成安全的文件名"""
    safe = "".join(
        c for c in title if c.isalnum() or c in (" ", "-", "_", "：", "、", "，", "。")
    ).strip()
    return safe if safe else "unnamed"


def convert_directory(input_dir: Path, output_dir: Path, directory_json: Path) -> None:
    """根据目录树结构转换飞书文档为 Markdown"""
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(directory_json, encoding="utf-8") as f:
        data = json.load(f)

    node_map = {}

    def process_node(node: dict, path_parts: list):
        title = node.get("title", "Untitled")
        obj_token = node.get("obj_token")

        if obj_token:
            node_map[obj_token] = (title, path_parts.copy())

        for child in node.get("children", []):
            process_node(child, path_parts + [title])

    for root_node in data.get("directory_tree", []):
        process_node(root_node, [])

    converted_count = 0
    for doc_file in input_dir.glob("*.json"):
        try:
            with open(doc_file, encoding="utf-8") as f:
                doc_data = json.load(f)

            obj_token = doc_data.get("obj_token")
            title = doc_data.get("title", doc_file.stem)

            if obj_token and obj_token in node_map:
                _, path_parts = node_map[obj_token]
            else:
                path_parts = []

            target_dir = output_dir
            for part in path_parts:
                target_dir = target_dir / get_safe_filename(part)

            target_dir.mkdir(parents=True, exist_ok=True)

            output_filename = get_safe_filename(title) + ".md"
            output_file = target_dir / output_filename

            markdown_content = convert_document_to_markdown(doc_file)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            print(f"✓ {title} -> {output_file.relative_to(output_dir)}")
            converted_count += 1

        except Exception as e:
            print(f"✗ Failed to convert {doc_file.name}: {e}")

    print(f"\nTotal: {converted_count} documents converted")


def generate_yaml_from_json(json_file: Path, yaml_file: Path) -> None:
    """从 JSON 目录结构生成 YAML 格式"""
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)

    def tree_to_yaml(nodes, indent=0):
        result = []
        for node in nodes:
            prefix = "  " * indent + "- "
            result.append(prefix + node["title"])
            if node.get("children"):
                result.extend(tree_to_yaml(node["children"], indent + 1))
        return result

    lines = ["# 飞书知识库目录结构", f"# 空间 ID: {data['space_id']}", ""]
    lines.extend(tree_to_yaml(data["directory_tree"]))

    with open(yaml_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✓ Generated: {yaml_file.name}")


def generate_jupyterbook_toc(json_file: Path, toc_file: Path) -> None:
    """生成 JupyterBook 兼容的 _toc.yml 文件"""
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)

    def node_to_toc(node: Dict[str, Any]) -> dict:
        safe_filename = get_safe_filename(node["title"])
        toc_entry = {"file": safe_filename}

        if node.get("children") and len(node["children"]) > 0:
            toc_entry["chapters"] = [node_to_toc(child) for child in node["children"]]

        return toc_entry

    toc_structure = []

    for node in data["directory_tree"]:
        if node.get("children") and len(node["children"]) > 1:
            part_entry = {
                "part": node["title"],
                "chapters": [node_to_toc(child) for child in node["children"]],
            }
            toc_structure.append(part_entry)
        else:
            toc_structure.append(node_to_toc(node))

    lines = [
        "# JupyterBook 目录结构",
        f"# 空间 ID: {data['space_id']}",
        "",
    ]

    def toc_to_yaml(entries, indent=0):
        result = []
        for entry in entries:
            prefix = "  " * indent

            if "part" in entry:
                result.append(f"{prefix}- part: {entry['part']}")
                result.append(f"{prefix}  chapters:")
                result.extend(toc_to_yaml(entry["chapters"], indent + 2))
            elif "chapters" in entry:
                result.append(f"{prefix}- file: {entry['file']}")
                result.append(f"{prefix}  chapters:")
                result.extend(toc_to_yaml(entry["chapters"], indent + 2))
            else:
                result.append(f"{prefix}- file: {entry['file']}")

        return result

    lines.extend(toc_to_yaml(toc_structure))

    with open(toc_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✓ Generated: {toc_file.name} ({len(toc_structure)} entries)")

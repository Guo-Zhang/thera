"""
飞书文档到 JupyterBook Markdown 转换器

将飞书文档的 JSON 格式转换为 JupyterBook 兼容的 Markdown 文件。
"""

import json
from pathlib import Path
from typing import Dict, Any, List


def block_type_to_markdown(block: Dict[str, Any]) -> str:
    """将飞书 block 转换为 Markdown

    Args:
        block: 飞书 block 数据

    Returns:
        str: Markdown 文本
    """
    block_type = block.get("block_type", 0)

    # block_type 对照飞书文档类型
    # 1: Page, 2: Text, 3: Heading1, 4: Heading2, 5: Heading3, 6: Heading4, 7: Heading5, 8: Heading6
    # 9: Heading7, 10: Heading8, 11: Heading9, 12: Bullet, 13: Ordered, 14: Quote, 15: Divider

    result = ""

    if block_type == 2:  # Text 段落
        result += text_block_to_markdown(block)
    elif block_type == 3:  # Heading1
        result += heading_block_to_markdown(block, 1)
    elif block_type == 4:  # Heading2
        result += heading_block_to_markdown(block, 2)
    elif block_type == 5:  # Heading3
        result += heading_block_to_markdown(block, 3)
    elif block_type == 6:  # Heading4
        result += heading_block_to_markdown(block, 4)
    elif block_type == 7:  # Heading5
        result += heading_block_to_markdown(block, 5)
    elif block_type == 8:  # Heading6
        result += heading_block_to_markdown(block, 6)
    elif block_type == 12:  # Bullet list
        result += bullet_block_to_markdown(block)
    elif block_type == 13:  # Ordered list
        result += ordered_block_to_markdown(block)
    elif block_type == 14:  # Quote
        result += quote_block_to_markdown(block)
    elif block_type == 15:  # Divider
        result += "\n---\n"
    # 其他类型暂不处理

    return result


def text_block_to_markdown(block: Dict[str, Any]) -> str:
    """文本块转换为 Markdown"""
    if "text" not in block or not block["text"]:
        return ""

    elements = block["text"].get("elements") if block["text"] else []
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


def heading_block_to_markdown(block: Dict[str, Any], level: int) -> str:
    """标题块转换为 Markdown"""
    if "text" not in block or not block["text"]:
        return ""

    elements = block["text"].get("elements") if block["text"] else []
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


def bullet_block_to_markdown(block: Dict[str, Any]) -> str:
    """无序列表块转换为 Markdown"""
    if "text" not in block or not block["text"]:
        return ""

    elements = block["text"].get("elements") if block["text"] else []
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


def ordered_block_to_markdown(block: Dict[str, Any]) -> str:
    """有序列表块转换为 Markdown"""
    if "text" not in block or not block["text"]:
        return ""

    elements = block["text"].get("elements") if block["text"] else []
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


def quote_block_to_markdown(block: Dict[str, Any]) -> str:
    """引用块转换为 Markdown"""
    if "text" not in block or not block["text"]:
        return ""

    elements = block["text"].get("elements") if block["text"] else []
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


def convert_document_to_markdown(doc_file: Path) -> str:
    """将飞书文档 JSON 转换为 Markdown

    Args:
        doc_file: 飞书文档 JSON 文件路径

    Returns:
        str: Markdown 内容
    """
    with open(doc_file, "r", encoding="utf-8") as f:
        doc_data = json.load(f)

    title = doc_data.get("title", "Untitled")
    blocks = doc_data.get("blocks", [])

    # 添加标题
    markdown = f"# {title}\n\n"

    # 转换每个 block
    for block in blocks:
        markdown += block_type_to_markdown(block)

    return markdown


def get_safe_filename(title: str) -> str:
    """生成安全的文件名"""
    safe = "".join(
        c for c in title if c.isalnum() or c in (" ", "-", "_", "：", "、", "，", "。")
    ).strip()
    return safe if safe else "unnamed"


def convert_directory_with_tree(
    input_dir: Path, output_dir: Path, directory_json: Path
) -> None:
    """根据目录树结构转换飞书文档为 Markdown

    Args:
        input_dir: 飞书文档 JSON 目录
        output_dir: 输出 Markdown 目录
        directory_json: 飞书目录结构 JSON 文件
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 读取目录树
    with open(directory_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 建立 node_token -> title 的映射
    node_map = {}  # obj_token -> (title, path_components)

    def process_node(node: dict, path_parts: list[str]):
        title = node.get("title", "Untitled")
        obj_token = node.get("obj_token")

        if obj_token:
            node_map[obj_token] = (title, path_parts.copy())

        # 递归处理子节点
        for child in node.get("children", []):
            process_node(child, path_parts + [title])

    for root_node in data.get("directory_tree", []):
        process_node(root_node, [])

    # 转换文档
    converted_count = 0
    for doc_file in input_dir.glob("*.json"):
        try:
            with open(doc_file, "r", encoding="utf-8") as f:
                doc_data = json.load(f)

            obj_token = doc_data.get("obj_token")
            title = doc_data.get("title", doc_file.stem)

            # 根据目录树确定输出路径
            if obj_token and obj_token in node_map:
                _, path_parts = node_map[obj_token]
            else:
                path_parts = []

            # 构建输出目录
            target_dir = output_dir
            for part in path_parts:
                target_dir = target_dir / get_safe_filename(part)

            target_dir.mkdir(parents=True, exist_ok=True)

            # 生成安全的文件名
            output_filename = get_safe_filename(title) + ".md"
            output_file = target_dir / output_filename

            # 转换并保存
            markdown_content = convert_document_to_markdown(doc_file)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            rel_path = output_file.relative_to(output_dir)
            print(f"✓ {title} -> {rel_path}")
            converted_count += 1

        except Exception as e:
            print(f"✗ Failed to convert {doc_file.name}: {e}")

    print(f"\nTotal: {converted_count} documents converted")


def generate_yaml_from_json(json_file: Path, yaml_file: Path) -> None:
    """从 JSON 目录结构生成 YAML 格式

    Args:
        json_file: JSON 目录结构文件
        yaml_file: 输出 YAML 文件
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    def tree_to_yaml(nodes, indent=0):
        result = []
        for node in nodes:
            prefix = "  " * indent + "- "
            result.append(prefix + node["title"])
            if node.get("children"):
                result.extend(tree_to_yaml(node["children"], indent + 1))
        return result

    lines = ["# 飞书知识库目录结构"]
    lines.append(f"# 空间 ID: {data['space_id']}")
    lines.append("")
    lines.extend(tree_to_yaml(data["directory_tree"]))

    with open(yaml_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✓ Generated: {yaml_file.name}")


def generate_jupyterbook_toc(json_file: Path, toc_file: Path) -> None:
    """生成 JupyterBook 兼容的 _toc.yml 文件

    Args:
        json_file: JSON 目录结构文件
        toc_file: 输出 _toc.yml 文件
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    def get_safe_filename(title: str) -> str:
        """生成安全的文件名"""
        # 移除或替换特殊字符，保留中文、字母、数字和基本符号
        safe = "".join(
            c
            for c in title
            if c.isalnum() or c in (" ", "-", "_", "：", "、", "，", "。")
        ).strip()
        return safe if safe else "unnamed"

    def node_to_toc(node: Dict[str, Any]) -> dict:
        """将飞书节点转换为 JupyterBook TOC 条目"""
        safe_filename = get_safe_filename(node["title"])
        toc_entry = {"file": safe_filename}

        if node.get("children") and len(node["children"]) > 0:
            # 如果有子节点，使用 chapters
            toc_entry["chapters"] = [node_to_toc(child) for child in node["children"]]

        return toc_entry

    # 生成 JupyterBook TOC
    toc_structure = []

    for node in data["directory_tree"]:
        # 判断是否应该作为 part（有多个子节点）
        if node.get("children") and len(node["children"]) > 1:
            part_entry = {
                "part": node["title"],
                "chapters": [node_to_toc(child) for child in node["children"]],
            }
            toc_structure.append(part_entry)
        else:
            # 直接作为文件或章节
            toc_structure.append(node_to_toc(node))

    # 生成 YAML
    lines = [
        "# JupyterBook 目录结构",
        "# 此文件由飞书文档自动生成",
        "# 空间 ID: " + data["space_id"],
        "",
    ]

    def toc_to_yaml(entries, indent=0):
        """将 TOC 结构转换为 YAML 格式"""
        result = []
        for entry in entries:
            prefix = "  " * indent

            if "part" in entry:
                # Part 结构
                result.append(f"{prefix}- part: {entry['part']}")
                result.append(f"{prefix}  chapters:")
                result.extend(toc_to_yaml(entry["chapters"], indent + 2))
            elif "chapters" in entry:
                # 有子章节的文件
                result.append(f"{prefix}- file: {entry['file']}")
                result.append(f"{prefix}  chapters:")
                result.extend(toc_to_yaml(entry["chapters"], indent + 2))
            else:
                # 普通文件
                result.append(f"{prefix}- file: {entry['file']}")

        return result

    lines.extend(toc_to_yaml(toc_structure))

    with open(toc_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✓ Generated: {toc_file.name} ({len(toc_structure)} entries)")


def main():
    """主函数"""
    # 设置路径
    script_dir = Path(__file__).parent.parent.parent
    data_dir = script_dir / "data"
    feishu_dir = data_dir / "feishu" / "documents"
    fiction_dir = data_dir / "docs" / "fiction"
    directory_json = feishu_dir.parent / "feishu_wiki_directory.json"
    directory_yaml = fiction_dir / "feishu_wiki_directory.yaml"
    fiction_toc = fiction_dir / "_toc.yml"

    print(f"Input directory: {feishu_dir}")
    print(f"Output directory: {fiction_dir}\n")

    if not feishu_dir.exists():
        print(f"ERROR: Input directory does not exist: {feishu_dir}")
        exit(1)

    print("Converting Feishu documents to Markdown format...\n")

    # 转换文档（保留目录结构）
    convert_directory_with_tree(feishu_dir, fiction_dir, directory_json)

    # 生成 YAML 目录
    if directory_json.exists():
        generate_yaml_from_json(directory_json, directory_yaml)

    # 生成 _toc.yml
    if directory_json.exists():
        generate_jupyterbook_toc(directory_json, fiction_toc)

    print(f"\n✓ Conversion completed!")
    print(f"✓ Markdown files saved to: {fiction_dir}")
    print(f"✓ Directory structure (YAML): {directory_yaml}")
    print(f"✓ TOC: {fiction_toc}")


if __name__ == "__main__":
    main()

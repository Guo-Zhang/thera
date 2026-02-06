"""
飞书知识库 API 客户端示例（使用 lark-oapi SDK）

本模块使用飞书官方 Python SDK (lark-oapi) 提供知识库 API 的客户端封装，主要用于：

核心功能:
- 认证管理: 使用 SDK 自动管理 tenant_access_token，无需手动处理缓存和刷新
- 知识空间节点查询: 获取知识空间下的节点列表和详细信息
- 目录树构建: 递归构建完整的知识库目录结构，支持多层级嵌套
- 数据持久化: 将获取的数据保存到本地存储目录

主要 API 功能:
1. build_directory_tree(): 递归构建知识库完整目录树
2. save_data_to_storage(): 将数据保存到本地 storage 目录

使用方式:
配置环境变量: APP_ID, APP_SECRET, SPACE_ID
运行脚本后将生成知识库目录树并保存到 data/storage/feishu_wiki_directory.json

依赖:
- lark-oapi: 飞书开放平台官方 Python SDK
- Python 3.10+

安装依赖:
    uv add lark-oapi
"""

import os
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from lark_oapi.api.wiki.v2 import (
    ListSpaceNodeRequest,
)
from lark_oapi.api.docx.v1 import (
    ListDocumentBlockRequest,
    GetDocumentBlockRequest,
)
import lark_oapi as lark

# === input params start
app_id = os.getenv("FEISHU_APP_ID")
app_secret = os.getenv("FEISHU_APP_SECRET")
space_id = os.getenv("FEISHU_EXAMPLE_SPACE_ID")
# === input params end

# === storage directories start
SCRIPT_DIR = Path(__file__).parent.parent
STORAGE_DIR = SCRIPT_DIR / "data" / "storage"
FEISHU_DIR = STORAGE_DIR / "feishu"
JUPYTERBOOK_DIR = STORAGE_DIR / "jupyterbook"

# 创建所有需要的目录
FEISHU_DIR.mkdir(parents=True, exist_ok=True)
JUPYTERBOOK_DIR.mkdir(parents=True, exist_ok=True)
# === storage directories end

# 创建 lark 客户端
def create_client() -> lark.Client:
    """创建飞书 API 客户端
    
    SDK 会自动管理 token 的获取、缓存和刷新
    """
    return lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.INFO) \
        .build()

def save_data_to_storage(subdir: str, filename: str, data: Any) -> None:
    """将数据保存到 data/storage 的指定子目录

    Args:
        subdir: 子目录名 ('feishu' 或 'jupyterbook')
        filename: 文件名
        data: 要保存的数据
    """
    try:
        target_dir = STORAGE_DIR / subdir
        filepath = target_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filepath}")
    except Exception as e:
        print(f"Warning: Failed to save data to storage: {e}", file=sys.stderr)

def style_to_dict(style) -> dict:
    """将 style 对象转换为可序列化的字典"""
    if style is None:
        return None
    return {
        "bold": getattr(style, 'bold', False),
        "italic": getattr(style, 'italic', False),
        "strikethrough": getattr(style, 'strikethrough', False),
        "underline": getattr(style, 'underline', False),
        "inline_code": getattr(style, 'inline_code', False),
        "link": getattr(style, 'link', None),
    }

def block_to_dict(block) -> dict:
    """将 block 对象转换为字典

    Args:
        block: Block 对象

    Returns:
        dict: block 数据字典
    """
    data = {
        "block_id": block.block_id,
        "block_type": block.block_type,
        "parent_id": block.parent_id if hasattr(block, 'parent_id') else None,
        "children": block.children if hasattr(block, 'children') else None,
    }

    # 添加 block 类型特定的内容
    if block.text is not None:
        data["text"] = {
            "style": style_to_dict(getattr(block.text, 'style', None)),
            "elements": []
        }
        if hasattr(block.text, 'elements') and block.text.elements:
            for elem in block.text.elements:
                elem_data = {"type": elem.type if hasattr(elem, 'type') else None}
                if hasattr(elem, 'text_run'):
                    elem_data["text_run"] = {
                        "content": getattr(elem.text_run, 'content', None),
                        "style": style_to_dict(getattr(elem.text_run, 'style', None)),
                    }
                data["text"]["elements"].append(elem_data)

    return data

def save_document_content(obj_token: str, title: str, client: lark.Client) -> None:
    """获取并保存文档内容（包含完整的 block 内容）

    Args:
        obj_token: 文档对象token
        title: 文档标题
        client: 飞书客户端
    """
    try:
        # 获取文档的所有块
        page_token = None
        block_dict = {}  # block_id -> block data

        while True:
            request = ListDocumentBlockRequest.builder() \
                .document_id(obj_token) \
                .page_size(100)

            if page_token:
                request.page_token(page_token)

            request = request.build()

            response = client.docx.v1.document_block.list(request)

            if not response.success():
                print(f"Warning: Failed to fetch document blocks for '{title}': {response.code} {response.msg}", file=sys.stderr)
                return

            if response.data and response.data.items:
                for block in response.data.items:
                    block_dict[block.block_id] = block_to_dict(block)

            if response.data.has_more and response.data.page_token:
                page_token = response.data.page_token
            else:
                break

        # 按顺序保存 blocks
        blocks_list = list(block_dict.values())

        # 保存完整文档数据
        doc_data = {
            "title": title,
            "obj_token": obj_token,
            "blocks": blocks_list
        }

        # 使用安全的文件名
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_title:
            safe_title = f"doc_{obj_token}"

        # 保存到飞书原始格式目录
        filepath = FEISHU_DIR / "documents" / f"{safe_title}.json"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, indent=2, ensure_ascii=False)

        print(f"  Saved: {title} ({len(blocks_list)} blocks)")

    except Exception as e:
        print(f"Warning: Failed to save document '{title}': {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

def list_space_nodes(
    client: lark.Client,
    space_id: str,
    parent_node_token: Optional[str] = None,
    page_token: Optional[str] = None,
    page_size: int = 50
):
    """获取知识空间子节点列表

    Args:
        client: 飞书客户端
        space_id: 知识空间ID
        parent_node_token: 父节点token，可选
        page_token: 分页token，可选
        page_size: 每页数量，默认50

    Returns:
        API 响应数据
    """
    request = ListSpaceNodeRequest.builder() \
        .space_id(space_id) \
        .page_size(page_size)

    if parent_node_token:
        request.parent_node_token(parent_node_token)
    if page_token:
        request.page_token(page_token)

    request = request.build()

    response = client.wiki.v2.space_node.list(request)

    if not response.success():
        print(f"ERROR: 获取知识空间子节点列表失败: {response.code} {response.msg}", file=sys.stderr)
        raise Exception(f"failed to get space nodes: {response.code} {response.msg}")

    return response.data

def get_node_detail(
    client: lark.Client, 
    node_token: str
):
    """获取节点详细信息

    Args:
        client: 飞书客户端
        node_token: 节点token

    Returns:
        节点信息
    """
    # 暂未实现，可按需添加
    pass

def build_directory_tree(
    client: lark.Client,
    space_id: str,
    parent_node_token: Optional[str] = None,
    save_docs: bool = True
) -> List[Dict[str, Any]]:
    """递归构建知识库目录树结构

    Args:
        client: 飞书客户端
        space_id: 知识空间ID
        parent_node_token: 父节点token，可选
        save_docs: 是否保存文档内容，默认True

    Returns:
        List[Dict[str, Any]]: 目录树结构列表
    """
    nodes = []
    page_token = None

    while True:
        # 获取当前层级的节点
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
                    "children": []
                }

                # 保存文档内容（仅针对 docx 类型）
                if save_docs and item.obj_type == "docx" and item.obj_token:
                    save_document_content(item.obj_token, item.title, client)

                # 如果有子节点，递归获取
                if item.has_child:
                    node_info["children"] = build_directory_tree(
                        client,
                        space_id,
                        item.node_token,
                        save_docs
                    )

                nodes.append(node_info)

        # 检查是否还有更多分页
        if result.has_more and result.page_token:
            page_token = result.page_token
        else:
            break

    return nodes

def main():
    """主函数"""
    # 验证必要参数
    if not app_id:
        print("ERROR: FEISHU_APP_ID environment variable is required", file=sys.stderr)
        exit(1)
    if not app_secret:
        print("ERROR: FEISHU_APP_SECRET environment variable is required", file=sys.stderr)
        exit(1)
    if not space_id:
        print("ERROR: FEISHU_EXAMPLE_SPACE_ID environment variable is required", file=sys.stderr)
        exit(1)

    print(f"Using APP_ID: {app_id}")
    print(f"Using SPACE_ID: {space_id}")
    print(f"Storage directory: {STORAGE_DIR}")
    print(f"  - Feishu format: {FEISHU_DIR}")
    print(f"  - JupyterBook format: {JUPYTERBOOK_DIR}\n")

    # 创建客户端（SDK 自动处理认证）
    client = create_client()
    print("Created lark-oapi client (authentication managed by SDK)\n")

    # 构建目录树并保存文档
    try:
        print("Fetching documents and content...\n")
        directory_tree = build_directory_tree(client, space_id, save_docs=True)

        # 输出为 JSON 格式
        output_data = {
            "space_id": space_id,
            "directory_tree": directory_tree,
            "total_nodes": len(directory_tree),
            "generated_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        print("\n=== Directory Tree Structure ===")
        print(json.dumps(output_data, indent=2, ensure_ascii=False))

        # 保存目录结构到两个子目录
        save_data_to_storage("feishu", "feishu_wiki_directory.json", output_data)
        save_data_to_storage("jupyterbook", "feishu_wiki_directory.json", output_data)

        print(f"\n✓ Directory saved to: {FEISHU_DIR}/feishu_wiki_directory.json")
        print(f"✓ Directory saved to: {JUPYTERBOOK_DIR}/feishu_wiki_directory.json")
        print(f"✓ Documents saved to: {FEISHU_DIR}/documents/")

    except Exception as e:
        print(f"ERROR: building directory tree failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()

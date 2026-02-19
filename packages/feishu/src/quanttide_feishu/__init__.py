"""
quanttide-feishu - 飞书知识库 Python SDK

核心功能:
- 认证管理: 使用 SDK 自动管理 tenant_access_token
- 知识空间节点查询: 获取知识空间下的节点列表和详细信息
- 文档到 JupyterBook 转换: 将飞书文档转换为 Markdown 格式
"""

__version__ = "0.1.0"

from .client import create_lark_client
from .converter import (
    convert_document_to_markdown,
    convert_directory,
    generate_jupyterbook_toc,
    generate_yaml_from_json,
)
from .wiki import build_directory_tree, list_space_nodes, save_document_content

__all__ = [
    "create_lark_client",
    "list_space_nodes",
    "build_directory_tree",
    "save_document_content",
    "convert_document_to_markdown",
    "convert_directory",
    "generate_yaml_from_json",
    "generate_jupyterbook_toc",
]

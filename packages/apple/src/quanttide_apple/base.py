"""
Apple 应用适配器基类

提供统一的接口抽象，用于与 Apple 系统应用（Notes, Contacts, Calendar 等）交互。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from .shortcuts import run_shortcut as _run_shortcut


class AppleAdapter(ABC):
    """
    Apple 应用适配器抽象基类

    子类需要实现 `app_name` 属性和 `fetch` 方法。
    """

    @property
    @abstractmethod
    def app_name(self) -> str:
        """对应的 Apple 应用名"""
        pass

    @abstractmethod
    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        获取数据

        Args:
            **kwargs: 子类特定的查询参数

        Returns:
            数据列表
        """
        pass

    def run_shortcut(
        self,
        name: str,
        input_data: Any = None,
        timeout: int = 120,
    ) -> Optional[str]:
        """
        通过 Shortcut 执行自定义操作

        Args:
            name: Shortcut 名称
            input_data: 输入数据
            timeout: 超时时间

        Returns:
            Shortcut 输出，未成功返回 None
        """
        return _run_shortcut(name, input_data=input_data, timeout=timeout)

    def run_shortcut_with_file(
        self,
        name: str,
        input_path: Path = None,
        output_path: Path = None,
        timeout: int = 120,
    ) -> Optional[str]:
        """
        通过 Shortcut 执行文件输入输出操作

        Args:
            name: Shortcut 名称
            input_path: 输入文件路径
            output_path: 输出文件路径
            timeout: 超时时间

        Returns:
            Shortcut 输出（如果未指定 output_path），否则返回 None
        """
        return _run_shortcut(
            name,
            input_path=input_path,
            output_path=output_path,
            timeout=timeout,
        )


class AppleResult:
    """标准化的 Apple 应用数据结果"""

    def __init__(self, data: Any, meta: Optional[Dict] = None):
        self.data = data
        self.meta = meta or {}

    @property
    def count(self) -> int:
        """数据条数"""
        if isinstance(self.data, list):
            return len(self.data)
        return 1 if self.data else 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "data": self.data,
            "meta": self.meta,
        }


def build_folder_tree(folders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    将扁平文件夹列表转换为树结构

    Args:
        folders: 扁平文件夹列表，每个包含 id, name, parent_id

    Returns:
        树结构化的文件夹列表
    """
    nodes: Dict[str, Dict[str, Any]] = {}
    for folder in folders:
        node = {
            "id": folder.get("id"),
            "name": folder.get("name"),
            "parent_id": folder.get("parent_id"),
            "note_count": folder.get("note_count", 0),
            "children": [],
        }
        folder_id = node["id"]
        if isinstance(folder_id, str) and folder_id:
            nodes[folder_id] = node

    roots: List[Dict[str, Any]] = []
    for node in nodes.values():
        parent_id = node.get("parent_id")
        if isinstance(parent_id, str) and parent_id in nodes:
            nodes[parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots

"""
Apple Contacts 适配器

提供 Apple Contacts（联系人）的数据访问功能。

注意：此模块为占位实现，后续版本将提供完整功能。
"""

from typing import Any, Dict, List

from .base import AppleAdapter


class ContactsAdapter(AppleAdapter):
    """Apple Contacts 联系人适配器"""

    @property
    def app_name(self) -> str:
        return "Contacts"

    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        获取联系人

        Args:
            **kwargs: 可选参数（如 group, limit 等）

        Returns:
            联系人列表
        """
        raise NotImplementedError("Contacts adapter is not yet implemented")


def get_contacts(limit: int = None) -> List[Dict[str, Any]]:
    """
    获取联系人列表（便捷函数）

    Args:
        limit: 限制数量

    Returns:
        联系人列表
    """
    raise NotImplementedError("Contacts adapter is not yet implemented")

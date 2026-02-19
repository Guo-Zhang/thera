"""
Apple Reminders 适配器

提供 Apple Reminders（提醒事项）的数据访问功能。

注意：此模块为占位实现，后续版本将提供完整功能。
"""

from typing import Any, Dict, List

from .base import AppleAdapter


class RemindersAdapter(AppleAdapter):
    """Apple Reminders 提醒事项适配器"""

    @property
    def app_name(self) -> str:
        return "Reminders"

    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        获取提醒事项

        Args:
            **kwargs: 可选参数（如 list, completed 等）

        Returns:
            提醒事项列表
        """
        raise NotImplementedError("Reminders adapter is not yet implemented")


def get_reminders(list: str = None, completed: bool = False) -> List[Dict[str, Any]]:
    """
    获取提醒事项（便捷函数）

    Args:
        list: 列表名称
        completed: 是否包含已完成的

    Returns:
        提醒事项列表
    """
    raise NotImplementedError("Reminders adapter is not yet implemented")

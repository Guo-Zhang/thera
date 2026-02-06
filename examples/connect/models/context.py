"""
thera.models.context 的 Docstring
"""

from enum import Enum

class AuthoritySource(str, Enum):
    """谁主导了这条信息？"""
    SYSTEM = "system"      # AI 自动推断
    USER = "user"          # 用户显式输入/修正
    NEGOTIATED = "negotiated"  # 双方协商确认 换成“共识“，协商是达成共识的过程。

class ConfirmationStatus(str, Enum):
    """当前是否达成共识？"""
    PENDING = "pending"    # 待确认（如自动推断结果）
    CONFIRMED = "confirmed"  # 已确认（用户接受或主动设置）
    DISPUTED = "disputed"  # 用户明确反对


class Context:
    """
    语境
    """

    def __init__(self) -> None:
        self.context = ""

    def update_context(self, new_info: str) -> None:
        """
        更新语境信息
        """
        self.context += "\n" + new_info

    def get_context(self) -> str:
        """
        获取当前语境信息
        """
        return self.context

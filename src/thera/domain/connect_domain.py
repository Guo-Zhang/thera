"""
连接域 - 对话系统、备忘录、便签
"""

from enum import Enum
from typing import Any

from thera.meta import Mode, ModeType


class AuthoritySource(str, Enum):
    """谁主导了这条信息？"""

    SYSTEM = "system"
    USER = "user"
    NEGOTIATED = "negotiated"


class ConfirmationStatus(str, Enum):
    """当前是否达成共识？"""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"


class Context:
    """语境"""

    def __init__(self) -> None:
        self.context = ""

    def update_context(self, new_info: str) -> None:
        self.context += "\n" + new_info

    def get_context(self) -> str:
        return self.context


class ConnectDomain(Mode):
    name = "connect"
    description = "连接域 - 对话、备忘录、便签"

    def __init__(self, app):
        super().__init__(app)
        self.context = Context()
        self.memos = []
        self.messages = []

    def on_activate(self):
        print(f"Activated: {self.name}")

    def on_deactivate(self):
        print(f"Deactivated: {self.name}")

    def handle_input(self, user_input: str) -> str:
        if user_input.startswith("/connect"):
            return self._handle_connect(user_input)
        return self._handle_chat(user_input)

    def _handle_connect(self, user_input: str) -> str:
        content = user_input.replace("/connect", "").strip()
        if not content:
            return f"Context: {self.context.get_context() or 'No context'}\nMemos: {len(self.memos)}"
        self.context.update_context(content)
        self.memos.append(content)
        return f"Connected: {content}"

    def _handle_chat(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})
        reply = f"[Connect] 已收到: {user_input}"
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def auto_switch(self, user_input: str) -> ModeType | None:
        if user_input.startswith("/think"):
            return ModeType.THINK
        if user_input.startswith("/write"):
            return ModeType.WRITE
        if user_input.startswith("/knowl"):
            return ModeType.KNOWL
        if user_input.startswith("/chat"):
            return ModeType.CHAT
        return None

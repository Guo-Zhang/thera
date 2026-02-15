"""
连接域 - Domain
"""

from enum import Enum

from thera.meta import Domain, DomainType


class AuthoritySource(str, Enum):
    SYSTEM = "system"
    USER = "user"
    NEGOTIATED = "negotiated"


class ConfirmationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"


class Context:
    def __init__(self) -> None:
        self.context = ""

    def update_context(self, new_info: str) -> None:
        self.context += "\n" + new_info

    def get_context(self) -> str:
        return self.context


class ConnectDomain(Domain):
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

    def auto_switch(self, user_input: str) -> DomainType | None:
        if user_input.startswith("/think"):
            return DomainType.THINK
        if user_input.startswith("/write"):
            return DomainType.WRITE
        if user_input.startswith("/knowl"):
            return DomainType.KNOWL
        if user_input.startswith("/chat"):
            return DomainType.CHAT
        return None

"""
写作域 - Domain
"""

from thera.meta import Domain, DomainType


class WriteDomain(Domain):
    name = "write"
    description = "写作域 - 小说创作、片段分析"

    def on_activate(self):
        print(f"Activated: {self.name}")

    def on_deactivate(self):
        print(f"Deactivated: {self.name}")

    def handle_input(self, user_input: str) -> str:
        return f"[Write] {user_input}"

    def auto_switch(self, user_input: str) -> DomainType | None:
        if user_input.startswith("/think"):
            return DomainType.THINK
        if user_input.startswith("/knowl"):
            return DomainType.KNOWL
        if user_input.startswith("/chat"):
            return DomainType.CHAT
        return None

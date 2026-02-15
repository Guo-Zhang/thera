from thera.meta import Mode, ModeType


class WriteDomain(Mode):
    name = "write"
    description = "写作域 - 小说创作、片段分析"

    def on_activate(self):
        print(f"Activated: {self.name}")

    def on_deactivate(self):
        print(f"Deactivated: {self.name}")

    def handle_input(self, user_input: str) -> str:
        return f"[Write] {user_input}"

    def auto_switch(self, user_input: str) -> ModeType | None:
        if user_input.startswith("/think"):
            return ModeType.THINK
        if user_input.startswith("/knowl"):
            return ModeType.KNOWL
        if user_input.startswith("/chat"):
            return ModeType.CHAT
        return None

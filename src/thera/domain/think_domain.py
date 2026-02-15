from thera.meta import Mode, ModeType


class ThinkDomain(Mode):
    name = "think"
    description = "思考域 - 头脑风暴、深度分析"

    def on_activate(self):
        print(f"Activated: {self.name}")

    def on_deactivate(self):
        print(f"Deactivated: {self.name}")

    def handle_input(self, user_input: str) -> str:
        return f"[Think] {user_input}"

    def auto_switch(self, user_input: str) -> ModeType | None:
        if user_input.startswith("/write"):
            return ModeType.WRITE
        if user_input.startswith("/knowl"):
            return ModeType.KNOWL
        if user_input.startswith("/chat"):
            return ModeType.CHAT
        return None

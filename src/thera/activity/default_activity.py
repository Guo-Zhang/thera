from thera.meta import Mode, ModeType
from thera.config import settings
from openai import OpenAI


class ChatDomain(Mode):
    name = "chat"
    description = "General conversation mode"

    def __init__(self, app):
        super().__init__(app)
        self.client = OpenAI(
            api_key=settings.llm_api_key, base_url=settings.llm_base_url
        )
        self.messages = [{"role": "system", "content": "你是一个友好的 AI 助手。"}]

    def on_activate(self):
        print(f"Activated: {self.name}")

    def on_deactivate(self):
        print(f"Deactivated: {self.name}")

    def handle_input(self, user_input: str) -> str:
        if user_input.startswith("/"):
            return "Use /mode <name> to switch modes"

        self.messages.append({"role": "user", "content": user_input})

        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=self.messages,
                temperature=0.7,
            )
            assistant_message = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": assistant_message})
            return assistant_message
        except Exception as e:
            return f"Error: {str(e)}"

    def auto_switch(self, user_input: str) -> ModeType | None:
        if user_input.startswith("/think"):
            return ModeType.THINK
        if user_input.startswith("/write"):
            return ModeType.WRITE
        if user_input.startswith("/knowl"):
            return ModeType.KNOWL
        return None

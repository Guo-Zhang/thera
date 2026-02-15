"""
Chat Activity - 默认对话活动

职责：
1. 和用户聊天
2. 意图识别：判断是否需要切换到其他 Domain/Activity/Asset/State
3. 引导用户切换
"""

from openai import OpenAI

from thera.config import settings
from thera.meta import Domain, DomainType


class DefaultActivity:
    """Default Activity - 默认对话活动"""

    name = "chat"
    description = "对话活动 - AI 聊天"

    def __init__(self, app):
        super().__init__(app)
        self.client = OpenAI(
            api_key=settings.llm_api_key, base_url=settings.llm_base_url
        )
        self.system_prompt = """你是一个友好的 AI 助手。

当用户想要：
- 头脑风暴、深度思考 → 建议切换到 /think 思考域
- 写作、小说创作 → 建议切换到 /write 写作域
- 知识发现、知识管理 → 建议切换到 /knowl 知识域
- 记录想法、保存备忘 → 建议切换到 /connect 连接域

如果用户明确要切换，直接返回 "SWITCH:域名称"，如 "SWITCH:think"
否则正常回复用户。"""

        self.messages = [{"role": "system", "content": self.system_prompt}]

    def on_activate(self):
        print(f"Activated: {self.name}")

    def on_deactivate(self):
        print(f"Deactivated: {self.name}")

    def handle_input(self, user_input: str) -> str:
        if user_input.startswith("/"):
            return self._handle_command(user_input)

        # 检查是否需要切换 Domain
        switch_domain = self._detect_domain_switch(user_input)
        if switch_domain:
            return switch_domain

        # 正常对话
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

    def _handle_command(self, user_input: str) -> str:
        """处理命令"""
        parts = user_input[1:].split()
        cmd = parts[0] if parts else ""

        if cmd in ["think", "write", "knowl", "connect", "chat"]:
            return f"SWITCH:{cmd}"

        return f"可用命令：/think /write /knowl /connect /chat"

    def _detect_domain_switch(self, user_input: str) -> str | None:
        """通过 LLM 检测是否需要切换 Domain"""
        # 简单的关键词检测
        switch_hints = {
            "connect": ["备忘", "记录", "便签", "memo", "保存", "想法"],
            "think": [
                "思考",
                "头脑风暴",
                "分析",
                "idea",
                "商业化",
                "获客",
                "市场",
                "渠道",
                "治理",
                "AI",
                "开发者",
                "技术",
                "模型",
            ],
            "write": ["写作", "小说", "创作", "写"],
            "knowl": ["知识", "发现", "相似度", "分析文档"],
        }

        for domain, keywords in switch_hints.items():
            for kw in keywords:
                if kw in user_input:
                    return f"我注意到你想聊【{domain}】相关的话题。\n切换到该领域：/domain {domain}\n或者继续当前对话？"

        return None

    def auto_switch(self, user_input: str) -> DomainType | None:
        """自动切换检测"""
        if user_input.startswith("/think"):
            return DomainType.THINK
        if user_input.startswith("/write"):
            return DomainType.WRITE
        if user_input.startswith("/knowl"):
            return DomainType.KNOWL
        if user_input.startswith("/connect"):
            return DomainType.CONNECT
        return None

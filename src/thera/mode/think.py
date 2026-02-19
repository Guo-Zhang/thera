"""
思考域 - Domain
"""

from datetime import datetime
from enum import Enum

from thera.meta import Domain, DomainType


class IdeaCategory(str, Enum):
    WORK = "work"
    LIFE = "life"
    UNKNOWN = "unknown"


class ThinkDomain(Domain):
    name = "think"
    description = "思考域 - 头脑风暴、深度分析"

    def __init__(self, app):
        super().__init__(app)
        self.ideas = []
        self.tools = ["brainstorm", "analyze", "reflect", "plan"]

    def on_activate(self):
        print(f"Activated: {self.name}")

    def on_deactivate(self):
        print(f"Deactivated: {self.name}")

    def handle_input(self, user_input: str) -> str:
        if user_input.startswith("/idea"):
            return self._handle_idea(user_input)
        if user_input.startswith("/brainstorm"):
            return self._handle_brainstorm(user_input)
        return f"[Think] {user_input}"

    def _handle_idea(self, user_input: str) -> str:
        content = user_input.replace("/idea", "").strip()
        if not content:
            return self._list_ideas()

        import re

        match = re.match(r"\[(\w+)\]\s*(.+)", content)
        if match:
            category = match.group(1)
            content = match.group(2)
        else:
            category = self.classify_idea(content)

        self.save_idea(content, category)
        return f"Idea saved: [{category}] {content}"

    def _handle_brainstorm(self, user_input: str) -> str:
        topic = user_input.replace("/brainstorm", "").strip()
        if not topic:
            return "Usage: /brainstorm <topic>"
        return f"[Brainstorm] Generating ideas for: {topic}"

    def _list_ideas(self) -> str:
        if not self.ideas:
            return "No ideas yet. Use /idea <content> to add one."

        lines = ["Ideas:"]
        for idea in self.ideas:
            lines.append(f"  - [{idea['category']}] {idea['content']}")
        return "\n".join(lines)

    def classify_idea(self, idea: str) -> str:
        work_keywords = [
            "项目",
            "会议",
            "报告",
            "客户",
            "邮件",
            "工作",
            "任务",
            "deadline",
            "演示",
            "方案",
            "需求",
            "开发者",
            "技术",
            "模型",
            "AI",
            "产品",
            "商业化",
            "获客",
            "市场",
            "渠道",
            "治理",
            "迭代",
            "认知",
        ]
        life_keywords = [
            "健身",
            "超市",
            "电影",
            "吃饭",
            "旅游",
            "朋友",
            "家庭",
            "购物",
            "娱乐",
            "休息",
            "运动",
            "生活",
        ]

        for kw in work_keywords:
            if kw in idea:
                return IdeaCategory.WORK.value

        for kw in life_keywords:
            if kw in idea:
                return IdeaCategory.LIFE.value

        return IdeaCategory.UNKNOWN.value

    def save_idea(self, content: str, category: str = "unknown"):
        idea = {
            "content": content,
            "category": category,
            "timestamp": datetime.now().isoformat(),
        }
        self.ideas.append(idea)

        if self.app and self.app.storage:
            ideas_data = self.app.storage.load_json("think", "ideas.json") or []
            ideas_data.append(idea)
            self.app.storage.save_json("think", "ideas.json", ideas_data)

    def get_tools(self) -> dict:
        return {
            "brainstorm": "头脑风暴，产生创意想法",
            "analyze": "深度分析问题",
            "reflect": "反思总结",
            "plan": "制定计划",
        }

    def auto_switch(self, user_input: str) -> DomainType | None:
        if user_input.startswith("/write"):
            return DomainType.WRITE
        if user_input.startswith("/knowl"):
            return DomainType.KNOWL
        if user_input.startswith("/chat"):
            return DomainType.CHAT
        return None

"""思考命令处理器"""

from datetime import datetime
from enum import Enum


class IdeaCategory(str, Enum):
    WORK = "work"
    LIFE = "life"
    UNKNOWN = "unknown"


_ideas: list[dict] = []


def handle(user_input: str) -> str:
    if user_input.startswith("/think"):
        user_input = user_input[6:].strip() or user_input

    if user_input.startswith("/idea"):
        return _handle_idea(user_input)
    if user_input.startswith("/brainstorm"):
        return _handle_brainstorm(user_input)
    if user_input.startswith("/think"):
        return f"[Think] {user_input}"
    return f"[Think] {user_input}"


def _handle_idea(user_input: str) -> str:
    content = user_input.replace("/idea", "").strip()
    if not content:
        return _list_ideas()

    import re

    match = re.match(r"\[(\w+)\]\s*(.+)", content)
    if match:
        category = match.group(1)
        content = match.group(2)
    else:
        category = _classify_idea(content)

    _save_idea(content, category)
    return f"Idea saved: [{category}] {content}"


def _handle_brainstorm(user_input: str) -> str:
    topic = user_input.replace("/brainstorm", "").strip()
    if not topic:
        return "Usage: /brainstorm <topic>"
    return f"[Brainstorm] Generating ideas for: {topic}"


def _list_ideas() -> str:
    if not _ideas:
        return "No ideas yet. Use /idea <content> to add one."

    lines = ["Ideas:"]
    for idea in _ideas:
        lines.append(f"  - [{idea['category']}] {idea['content']}")
    return "\n".join(lines)


def _classify_idea(idea: str) -> str:
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


def _save_idea(content: str, category: str = "unknown"):
    idea = {
        "content": content,
        "category": category,
        "timestamp": datetime.now().isoformat(),
    }
    _ideas.append(idea)

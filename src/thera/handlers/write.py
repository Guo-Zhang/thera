"""写作命令处理器"""


def handle(user_input: str) -> str:
    if user_input.startswith("/write"):
        user_input = user_input[6:].strip() or user_input
    return f"[Write] {user_input}"

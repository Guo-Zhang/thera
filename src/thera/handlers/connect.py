"""连接命令处理器"""

_context: str = ""
_memos: list[str] = []
_messages: list[dict] = []


def handle(user_input: str) -> str:
    if user_input.startswith("/connect"):
        return _handle_connect(user_input)
    return _handle_chat(user_input)


def _handle_connect(user_input: str) -> str:
    global _context
    content = user_input.replace("/connect", "").strip()
    if not content:
        return f"Context: {_context or 'No context'}\nMemos: {len(_memos)}"
    _context += "\n" + content
    _memos.append(content)
    return f"Connected: {content}"


def _handle_chat(user_input: str) -> str:
    global _messages
    _messages.append({"role": "user", "content": user_input})
    reply = f"[Connect] 已收到: {user_input}"
    _messages.append({"role": "assistant", "content": reply})
    return reply

"""
thera.screens.dialogue_screen 的 Docstring
"""
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Input, Static, ListView, ListItem, Footer


class DialogueScreen(Screen):
    """主对话界面：左侧聊天 + 右侧便签列表"""

    CSS = """
    #chat-container {
        width: 70%;
        height: 100%;
        border-right: solid #444;
    }

    #notes-container {
        width: 30%;
        height: 100%;
        padding: 1 2;
    }

    #chat-history {
        height: 1fr;
        overflow-y: auto;
        scrollbar-size-vertical: 1;
    }

    .user-message {
        background: #4a6fa5;
        color: white;
        padding: 1 2;
        margin: 1 2 1 10;
        width: 80%;
        text-align: right;
    }

    .ai-message {
        background: #333;
        color: #ddd;
        padding: 1 2;
        margin: 1 10 1 2;
        width: 80%;
        text-align: left;
    }

    #user-input {
        height: auto;
        padding: 1 2;
    }

    #notes-title {
        text-style: bold;
        margin-bottom: 1;
    }

    ListView {
        height: 1fr;
    }

    ListItem {
        padding: 1 0;
    }

    ListItem:hover {
        background: #2a2a2a;
    }
    """

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                ScrollableContainer(id="chat-history"),
                Input(placeholder="请输入您的问题...", id="user-input"),
                id="chat-container"
            ),
            Vertical(
                Static("📌 便签列表", id="notes-title"),
                ListView(id="notes-list"),
                id="notes-container"
            ),
        )
        yield Footer()

    def on_mount(self):
        self.add_ai_message("您好！我是您的 AI 笔记助手。请输入内容开始对话。")

    def add_user_message(self, content: str):
        chat = self.query_one("#chat-history")
        msg = Static(content, classes="user-message")
        chat.mount(msg)
        chat.scroll_end(animate=False)

    def add_ai_message(self, content: str):
        chat = self.query_one("#chat-history")
        msg = Static(content, classes="ai-message")
        chat.mount(msg)
        chat.scroll_end(animate=False)

    @on(Input.Submitted, "#user-input")
    def handle_input(self, event: Input.Submitted):
        user_text = event.value.strip()
        if not user_text:
            return

        # 清空输入框
        input_widget = self.query_one("#user-input", Input)
        input_widget.value = ""

        # 显示用户消息
        self.add_user_message(user_text)

        # 🧠 Mock AI 回复
        ai_reply = f"我收到了您的消息：「{user_text}」。这是一个模拟回复。"
        self.add_ai_message(ai_reply)

        # 💡 自动保存为便签
        notes_list = self.query_one("#notes-list", ListView)
        note_summary = f"• {ai_reply[:40]}..."
        notes_list.append(ListItem(Static(note_summary)))
class DialogueApp(App):
    """主应用入口"""

    def on_mount(self):
        self.push_screen(DialogueScreen())


if __name__ == "__main__":
    DialogueApp().run()

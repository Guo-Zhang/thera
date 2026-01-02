"""
消息视图 - 独立可运行的对话流组件
"""

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, TextArea, RichLog, Footer
from textual.binding import Binding


class MessageContext(Static):
    def __init__(self, context: str = "", **kwargs):
        super().__init__(context, **kwargs)
        self.styles.height = 6
        self.styles.background = "#252525"
        self.styles.border = ("round", "green")


class MessageList(RichLog):
    def __init__(self, **kwargs):
        super().__init__(auto_scroll=True, wrap=True, max_lines=100, **kwargs)
        self.styles.height = 12


class InputBar(TextArea):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.placeholder = "在此继续对话...（Ctrl+J 发送）"
        self.styles.height = 5


class MessagePanel(Vertical):
    def compose(self) -> ComposeResult:
        yield MessageContext(
            "协作模式：AI 外脑辅助\n目标：构思新场景\n约束：避开经典IP"
        )
        self.message_list = MessageList()
        yield self.message_list
        self.input_bar = InputBar()
        yield self.input_bar

    def on_mount(self) -> None:
        self.input_bar.focus()

    def send_message(self) -> None:
        """核心发送逻辑，供外部调用"""
        text = self.input_bar.text.strip()
        if text:
            self.message_list.write(f"[bold green]You:[/]: {text}")
            self.message_list.write(f"[bold blue]AI:[/]: 已收到，正在分析语境...")
            self.input_bar.text = ""
            self.input_bar.focus()  # 发送后重新聚焦


class MessageScreen(App):
    """独立的消息视图应用"""
    BINDINGS = [
        Binding("ctrl+j", "send_message", "发送"),
        Binding("escape", "quit", "退出"),
    ]

    def compose(self) -> ComposeResult:
        yield MessagePanel()
        yield Footer()

    def action_send_message(self) -> None:
        """App 层动作：委托给 MessagePanel"""
        message_panel = self.query_one(MessagePanel)
        message_panel.send_message()

    def action_quit(self) -> None:
        self.exit()


def main() -> None:
    app = MessageScreen()
    app.run()


if __name__ == "__main__":
    main()

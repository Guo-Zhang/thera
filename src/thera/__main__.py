from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, TextArea, RichLog, Footer
from textual.binding import Binding


class MemoContext(Static):
    def __init__(self, context: str = "", **kwargs):
        super().__init__(context, **kwargs)
        self.styles.height = 6
        self.styles.background = "#1e1e1e"
        self.styles.border = ("round", "blue")


class Memo(TextArea):
    def __init__(self, content: str = "", **kwargs):
        super().__init__(text=content, **kwargs)
        self.show_line_numbers = False
        self.styles.height = 12


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


class MemoPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield MemoContext("领域：小说\n子类：杭城言情\n类型：场景设定\n状态：草稿")
        yield Memo("女主在龙井村采茶时接到前男友电话。")


class MessagePanel(Vertical):
    def compose(self) -> ComposeResult:
        yield MessageContext("协作模式：AI 外脑辅助\n目标：构思新场景\n约束：避开经典IP")
        self.message_list = MessageList()
        yield self.message_list
        self.input_bar = InputBar()
        yield self.input_bar

    def on_mount(self) -> None:
        self.input_bar.focus()

    def action_send_message(self) -> None:
        text = self.input_bar.text.strip()
        if text:
            self.message_list.write(f"[bold green]You:[/]: {text}")
            self.message_list.write(f"[bold blue]AI:[/]: 已收到，正在分析语境...")
            self.input_bar.text = ""


class MemoScreen(Horizontal):
    def compose(self) -> ComposeResult:
        yield MemoPanel()
        yield MessagePanel()


class TheraApp(App):
    CSS = """
    Screen { layout: horizontal; }
    MemoPanel { width: 40%; height: 100%; }
    MessagePanel { width: 60%; height: 100%; }
    """
    BINDINGS = [
        Binding("ctrl+s", "save", "保存"),
        Binding("ctrl+j", "send_message", "发送"),  # ← 关键：绑定发送快捷键
        Binding("escape", "quit", "退出"),
    ]

    def compose(self) -> ComposeResult:
        yield MemoScreen()
        yield Footer()

    def action_save(self):
        self.notify("备忘已保存（模拟）", title="成功")

    def action_send_message(self):
        # 将动作委托给 MessagePanel
        message_panel = self.query_one(MessagePanel)
        message_panel.action_send_message()

    def action_quit(self):
        self.exit()


if __name__ == "__main__":
    TheraApp().run()
from __future__ import annotations

import sys
from pathlib import Path
from enum import Enum


class ActivityType(Enum):
    CHAT = "chat"
    THINK = "think"
    WRITE = "write"
    KNOWL = "knowl"
    CONNECT = "connect"


class Thera:
    def __init__(self, storage_path: Path | None = None):
        self.storage_path = storage_path or self._default_storage_path()
        self._activity_manager = None
        self._domain_manager = None
        self._storage = None
        self._current_activity = None

    @staticmethod
    def _default_storage_path() -> Path:
        home = Path.home()
        return home / "thera"

    def init(self):
        self.storage_path.mkdir(parents=True, exist_ok=True)
        from thera.meta import DomainManager, StorageState
        from thera.activity.manager import ActivityManager

        self._storage = StorageState(self.storage_path)
        self._storage.ensure_dirs()

        self._activity_manager = ActivityManager(self)
        self._activity_manager.register_default_activities()

        self._domain_manager = DomainManager(self)
        self._domain_manager.register_default_domains()

    @property
    def activity_manager(self):
        if not self._activity_manager:
            raise RuntimeError("Thera not initialized. Call init() first.")
        return self._activity_manager

    @property
    def domain_manager(self):
        if not self._domain_manager:
            raise RuntimeError("Thera not initialized. Call init() first.")
        return self._domain_manager

    @property
    def storage(self):
        if not self._storage:
            raise RuntimeError("Thera not initialized. Call init() first.")
        return self._storage

    def switch_activity(self, activity_type: str):
        if not self._activity_manager:
            raise RuntimeError("Thera not initialized. Call init() first.")
        self._activity_manager.switch_activity(activity_type)

    def run(self, activity: str | None = None):
        from textual.app import App, ComposeResult
        from textual.containers import Container, VerticalScroll
        from textual.widgets import Header, Footer, Input, Static

        class TUIApp(App):
            CSS = """
            Screen {
                layout: vertical;
            }
            #chat-history {
                height: 100%;
                background: $surface;
                padding: 1;
            }
            #user-input {
                dock: bottom;
            }
            """

            def __init__(self, thera):
                super().__init__()
                self.thera = thera
                self.activity = "chat"
                self._chat_content = ""

            def compose(self) -> ComposeResult:
                yield Header()
                yield Container(VerticalScroll(Static(id="chat-history", markup=True)))
                yield Input(placeholder="Type your message...", id="user-input")
                yield Footer()

            def on_mount(self):
                self.thera.activity_manager.switch_activity(self.activity)
                self._update_chat("Welcome to Thera!\n")

            def _update_chat(self, text: str):
                self._chat_content += text
                self.query_one("#chat-history").update(self._chat_content)

            def on_input_submitted(self, event: Input.Submitted):
                user_input = event.value
                if not user_input:
                    return

                self._update_chat(f"\n> {user_input}\n")

                # 先处理 Activity 的自动切换
                suggested = self.thera.activity_manager.auto_switch(user_input)
                if suggested:
                    self.thera.activity_manager.switch_activity(suggested.value)
                    self._update_chat(f"[切换到 {suggested.value} 活动]\n")

                # 处理输入
                response = self.thera.activity_manager.handle_input(user_input)
                self._update_chat(f"{response}\n")

                event.value = ""

        app = TUIApp(thera=self)
        if activity:
            self.switch_activity(activity)
        app.run()


_app_instance: Thera | None = None


def get_app() -> Thera:
    global _app_instance
    if _app_instance is None:
        _app_instance = Thera()
        _app_instance.init()
    return _app_instance


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Thera - AI Assistant")
    parser.add_argument(
        "--activity",
        "-a",
        choices=["think", "write", "knowl", "chat", "connect"],
        help="Start in specific activity",
    )
    parser.add_argument(
        "--storage",
        "-s",
        type=Path,
        help="Custom storage path (default: ~/thera)",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="thera 0.1.0",
    )
    args = parser.parse_args()

    app = Thera(storage_path=args.storage)
    app.init()

    app.run(activity=args.activity)


if __name__ == "__main__":
    main()

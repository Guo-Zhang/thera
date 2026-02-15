from __future__ import annotations

import sys
from pathlib import Path


class Thera:
    def __init__(self, storage_path: Path | None = None):
        self.storage_path = storage_path or self._default_storage_path()
        self._mode_manager = None
        self._storage_manager = None
        self._current_mode = None

    @staticmethod
    def _default_storage_path() -> Path:
        home = Path.home()
        return home / "thera"

    def init(self):
        self.storage_path.mkdir(parents=True, exist_ok=True)
        from thera.meta import ModeManager, StorageManager

        self._storage_manager = StorageManager(self.storage_path)
        self._storage_manager.ensure_dirs()
        self._mode_manager = ModeManager(self)
        self._mode_manager.register_default_modes()

    @property
    def mode_manager(self):
        if not self._mode_manager:
            raise RuntimeError("Thera not initialized. Call init() first.")
        return self._mode_manager

    @property
    def storage(self):
        if not self._storage_manager:
            raise RuntimeError("Thera not initialized. Call init() first.")
        return self._storage_manager

    def switch_mode(self, mode_type: str):
        if not self._mode_manager:
            raise RuntimeError("Thera not initialized. Call init() first.")
        self._mode_manager.switch_mode(mode_type)

    def run(self, mode: str | None = None):
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
                self.mode = "chat"
                self._chat_content = ""

            def compose(self) -> ComposeResult:
                yield Header()
                yield Container(VerticalScroll(Static(id="chat-history", markup=True)))
                yield Input(placeholder="Type your message...", id="user-input")
                yield Footer()

            def on_mount(self):
                self.thera.mode_manager.switch_mode(self.mode)
                self._update_chat("Welcome to Thera!\n")

            def _update_chat(self, text: str):
                self._chat_content += text
                self.query_one("#chat-history").update(self._chat_content)

            def on_input_submitted(self, event: Input.Submitted):
                user_input = event.value
                if not user_input:
                    return

                self._update_chat(f"\n> {user_input}\n")

                response = self.thera.mode_manager.handle_input(user_input)
                self._update_chat(f"{response}\n")

                event.value = ""

        app = TUIApp(thera=self)
        if mode:
            self.switch_mode(mode)
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
        "--mode",
        "-m",
        choices=["think", "write", "knowl", "chat"],
        help="Start in specific mode",
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

    app.run(mode=args.mode)


if __name__ == "__main__":
    main()

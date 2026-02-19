from __future__ import annotations

import json
import yaml
from enum import Enum
from pathlib import Path
from typing import Callable


class StorageState:
    """存储状态管理器，限制操作范围在 thera 文件夹内"""

    def __init__(self, base_path: Path):
        self._base_path = base_path
        self._validate_path(base_path)
        self.base_path = base_path

    def _validate_path(self, path: Path):
        """验证路径是否在 thera 文件夹内"""
        if not str(path).startswith(str(self._base_path)):
            raise ValueError(f"Path {path} is outside thera folder")

    @property
    def allowed_paths(self) -> list[str]:
        """允许访问的路径列表"""
        return [str(self.base_path)]

    def ensure_dirs(self, *paths: str):
        """确保目录存在"""
        for p in paths:
            full_path = self._base_path / p
            self._validate_path(full_path)
            full_path.mkdir(parents=True, exist_ok=True)

    def get_data_dir(self, category: str) -> Path:
        """获取数据目录"""
        path = self.base_path / category
        self._validate_path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_json(self, category: str, filename: str, data: dict):
        """保存 JSON 文件"""
        path = self.get_data_dir(category) / filename
        self._validate_path(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_json(self, category: str, filename: str) -> dict | None:
        """加载 JSON 文件"""
        path = self.get_data_dir(category) / filename
        self._validate_path(path)
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def save_yaml(self, category: str, filename: str, data: dict):
        """保存 YAML 文件"""
        path = self.get_data_dir(category) / filename
        self._validate_path(path)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)

    def load_yaml(self, category: str, filename: str) -> dict | None:
        """加载 YAML 文件"""
        path = self.get_data_dir(category) / filename
        self._validate_path(path)
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)


class Thera:
    def __init__(self, storage_path: Path | None = None):
        self.storage_path = storage_path or self._default_storage_path()
        self._storage = None
        self._handlers: dict[str, Callable] = {}
        self._current_handler: Callable | None = None
        self._history: list[dict] = []

    @staticmethod
    def _default_storage_path() -> Path:
        home = Path.home()
        return home / "thera"

    def init(self):
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._storage = StorageState(self.storage_path)
        self._storage.ensure_dirs()
        self._register_default_handlers()

    def _register_default_handlers(self):
        from thera.handlers import think, write, knowl, connect

        self.register("/think", think.handle)
        self.register("/write", write.handle)
        self.register("/knowl", knowl.handle)
        self.register("/connect", connect.handle)

    def register(self, command: str, handler: Callable):
        self._handlers[command] = handler

    def handle(self, user_input: str) -> str:
        self._history.append({"role": "user", "content": user_input})

        cmd = user_input.split()[0] if user_input else ""

        if cmd in self._handlers:
            self._current_handler = self._handlers[cmd]
            response = self._current_handler(user_input)
        elif self._current_handler:
            response = self._current_handler(user_input)
        else:
            response = "请输入命令（如 /think, /write）或选择领域"

        self._history.append({"role": "assistant", "content": response})
        return response

    def run(self, initial_command: str | None = None):
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
                self._chat_content = ""

            def compose(self) -> ComposeResult:
                yield Header()
                yield Container(VerticalScroll(Static(id="chat-history", markup=True)))
                yield Input(
                    placeholder="输入命令（如 /think, /write）...", id="user-input"
                )
                yield Footer()

            def on_mount(self):
                self._update_chat("Welcome to Thera!\n")
                self._update_chat("可用命令: /think, /write, /knowl, /connect\n\n")

            def _update_chat(self, text: str):
                self._chat_content += text
                self.query_one("#chat-history").update(self._chat_content)

            def on_input_submitted(self, event: Input.Submitted):
                user_input = event.value
                if not user_input:
                    return

                self._update_chat(f"\n> {user_input}\n")

                response = self.thera.handle(user_input)
                self._update_chat(f"{response}\n")

                event.value = ""

        app = TUIApp(thera=self)
        if initial_command:
            self.handle(initial_command)
        app.run()

    @property
    def storage(self):
        if not self._storage:
            raise RuntimeError("Thera not initialized. Call init() first.")
        return self._storage


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
        "--command",
        "-c",
        help="Initial command (e.g., /think, /write)",
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

    app.run(initial_command=args.command)


if __name__ == "__main__":
    main()

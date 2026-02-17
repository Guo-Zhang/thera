from __future__ import annotations

import json
import yaml
from enum import Enum
from pathlib import Path


class DomainType(Enum):
    CHAT = "chat"
    THINK = "think"
    WRITE = "write"
    KNOWL = "knowl"
    CONNECT = "connect"


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
        self._domain_manager = None
        self._storage = None
        self._current_domain = None

    @staticmethod
    def _default_storage_path() -> Path:
        home = Path.home()
        return home / "thera"

    def init(self):
        from thera.meta import DomainManager

        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._storage = StorageState(self.storage_path)
        self._storage.ensure_dirs()

        self._domain_manager = DomainManager(self)
        self._domain_manager.register_default_domains()

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

    def switch_domain(self, domain_type: str):
        if not self._domain_manager:
            raise RuntimeError("Thera not initialized. Call init() first.")
        self._domain_manager.switch_domain(domain_type)

    def run(self, domain: str | None = None):
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
                self.domain = "chat"
                self._chat_content = ""

            def compose(self) -> ComposeResult:
                yield Header()
                yield Container(VerticalScroll(Static(id="chat-history", markup=True)))
                yield Input(placeholder="Type your message...", id="user-input")
                yield Footer()

            def on_mount(self):
                self.thera.domain_manager.switch_domain(self.domain)
                self._update_chat("Welcome to Thera!\n")

            def _update_chat(self, text: str):
                self._chat_content += text
                self.query_one("#chat-history").update(self._chat_content)

            def on_input_submitted(self, event: Input.Submitted):
                user_input = event.value
                if not user_input:
                    return

                self._update_chat(f"\n> {user_input}\n")

                suggested = self.thera.domain_manager.auto_switch(user_input)
                if suggested:
                    self.thera.domain_manager.switch_domain(suggested.value)
                    self._update_chat(f"[切换到 {suggested.value} 领域]\n")

                response = self.thera.domain_manager.handle_input(user_input)
                self._update_chat(f"{response}\n")

                event.value = ""

        app = TUIApp(thera=self)
        if domain:
            self.switch_domain(domain)
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
        "--domain",
        "-d",
        choices=["think", "write", "knowl", "chat", "connect"],
        help="Start in specific domain",
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

    app.run(domain=args.domain)


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import yaml
from pathlib import Path


class StorageState:
    """存储状态管理器，限制操作范围在 thera 文件夹内"""

    def __init__(self, base_path: Path):
        self._base_path = base_path
        self._validate_path(base_path)
        self.base_path = base_path

    def _validate_path(self, path: Path):
        """验证路径是否在外"""
        if not str(path).startswith(str(self._base_path)):
            raise ValueError(f"Path {path} is outside thera folder")

    @property
    def allowed_paths(self) -> list[str]:
        return [str(self.base_path)]

    def ensure_dirs(self, *paths: str):
        for p in paths:
            full_path = self._base_path / p
            self._validate_path(full_path)
            full_path.mkdir(parents=True, exist_ok=True)

    def get_data_dir(self, category: str) -> Path:
        path = self.base_path / category
        self._validate_path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_json(self, category: str, filename: str, data: dict):
        path = self.get_data_dir(category) / filename
        self._validate_path(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_json(self, category: str, filename: str) -> dict | None:
        path = self.get_data_dir(category) / filename
        self._validate_path(path)
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def save_yaml(self, category: str, filename: str, data: dict):
        path = self.get_data_dir(category) / filename
        self._validate_path(path)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)

    def load_yaml(self, category: str, filename: str) -> dict | None:
        path = self.get_data_dir(category) / filename
        self._validate_path(path)
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)


class Thera:
    def __init__(self, storage_path: Path | None = None, workspace: str = "default"):
        self.storage_path = storage_path or self._default_storage_path()
        self.workspace = workspace
        self.workspace_path = self.storage_path / workspace
        self._storage = None

    @staticmethod
    def _default_storage_path() -> Path:
        home = Path.home()
        return home / "thera"

    def init(self):
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self._storage = StorageState(self.workspace_path)
        self._storage.ensure_dirs()

    def run(self):
        from textual.app import App, ComposeResult
        from textual.containers import Container, VerticalScroll
        from textual.widgets import Header, Footer, Input, Static

        class TUIApp(App):
            CSS = """
            Screen { layout: vertical; }
            #chat-history {
                height: 100%;
                background: $surface;
                padding: 1;
            }
            #user-input { dock: bottom; }
            """

            def __init__(self, thera):
                super().__init__()
                self.thera = thera

            def compose(self) -> ComposeResult:
                yield Header()
                yield Container(VerticalScroll(Static(id="chat-history", markup=True)))
                yield Input(placeholder="输入消息...", id="user-input")
                yield Footer()

            def on_mount(self):
                ws = self.thera.workspace
                self.query_one("#chat-history").update(
                    f"Welcome to Thera! [workspace: {ws}]\n"
                )

        app = TUIApp(thera=self)
        app.run()

    @property
    def storage(self):
        if not self._storage:
            raise RuntimeError("Thera not initialized. Call init() first.")
        return self._storage


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Thera - AI Assistant")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 默认活动子命令
    default_parser = subparsers.add_parser("default", help="增量式被动观察")
    default_parser.add_argument("file", help="日志文件路径")
    default_parser.add_argument(
        "--config", "-c", default="config.yaml", help="配置文件路径"
    )

    # TUI 模式
    parser.add_argument("--storage", "-s", type=Path, help="Custom storage path")
    parser.add_argument(
        "--workspace", "-w", default="default", help="Workspace name (default: default)"
    )
    parser.add_argument("--version", "-v", action="version", version="thera 0.1.0")
    args = parser.parse_args()

    # 处理 default 子命令
    if args.command == "default":
        import sys
        from pathlib import Path

        # 直接导入 default 模块，绕过 mode/__init__.py
        default_module_path = Path(__file__).parent / "mode" / "default.py"
        spec = __import__("importlib.util").util.spec_from_file_location(
            "default_module", default_module_path
        )
        default_module = __import__("importlib.util").util.module_from_spec(spec)
        sys.modules["default_module"] = default_module
        spec.loader.exec_module(default_module)

        config = default_module.load_default_config(args.config)
        processor = default_module.JournalProcessor(config)
        processor.process(args.file)
        return

    # 默认启动 TUI
    app = Thera(storage_path=args.storage, workspace=args.workspace)
    app.init()
    app.run()


if __name__ == "__main__":
    main()

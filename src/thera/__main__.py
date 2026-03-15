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
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Thera - AI Assistant")
    parser.add_argument("file", nargs="?", help="日志文件路径（用于 default 命令）")
    parser.add_argument("command", nargs="?", help="子命令（default 或空）")
    parser.add_argument("--storage", "-s", type=Path, help="Custom storage path")
    parser.add_argument(
        "--workspace", "-w", default="default", help="Workspace name (default: default)"
    )
    parser.add_argument("--version", "-v", action="version", version="thera 0.1.0")
    parser.add_argument("--config", "-c", default="config.yaml", help="配置文件路径")
    args = parser.parse_args()

    # 处理 default 子命令
    if args.file and not args.file.startswith("-"):
        # file 参数是位置参数，检查是否是 default 命令
        import sys

        sys.path.insert(0, str(Path(__file__).parent / "mode"))

        from default import JournalProcessor, load_default_config

        config = load_default_config(args.config)
        processor = JournalProcessor(config)
        processor.process(args.file)
        return

    # 默认启动 TUI
    app = Thera(storage_path=args.storage, workspace=args.workspace)
    app.init()
    app.run()


if __name__ == "__main__":
    main()

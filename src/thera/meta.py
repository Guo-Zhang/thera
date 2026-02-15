from __future__ import annotations

import json
import yaml
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path


class StorageManager:
    def __init__(self, base_path: Path):
        self.base_path = base_path

    def ensure_dirs(self):
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_data_dir(self, category: str) -> Path:
        path = self.base_path / category
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_json(self, category: str, filename: str, data: dict):
        path = self.get_data_dir(category) / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_json(self, category: str, filename: str) -> dict | None:
        path = self.get_data_dir(category) / filename
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def save_yaml(self, category: str, filename: str, data: dict):
        path = self.get_data_dir(category) / filename
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)

    def load_yaml(self, category: str, filename: str) -> dict | None:
        path = self.get_data_dir(category) / filename
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)


class ModeType(Enum):
    CHAT = "chat"
    THINK = "think"
    WRITE = "write"
    KNOWL = "knowl"


class Mode(ABC):
    name: str = ""
    description: str = ""

    def __init__(self, app):
        self.app = app

    @abstractmethod
    def handle_input(self, user_input: str) -> str:
        pass

    @abstractmethod
    def on_activate(self):
        pass

    @abstractmethod
    def on_deactivate(self):
        pass

    def auto_switch(self, user_input: str) -> ModeType | None:
        return None


class ModeManager:
    def __init__(self, app):
        self.app = app
        self._modes: dict = {}
        self._current_mode = None

    def register(self, mode_type: str, mode_class):
        self._modes[mode_type] = mode_class

    def register_default_modes(self):
        from thera.activity.default_activity import ChatDomain
        from thera.domain.connect_domain import ConnectDomain
        from thera.domain.knowl_domain import KnowlDomain
        from thera.domain.think_domain import ThinkDomain
        from thera.domain.write_domain import WriteDomain

        self.register("chat", ChatDomain)
        self.register("think", ThinkDomain)
        self.register("write", WriteDomain)
        self.register("knowl", KnowlDomain)
        self.register("connect", ConnectDomain)

    def switch_mode(self, mode_type: str):
        if self._current_mode:
            self._current_mode.on_deactivate()

        if mode_type not in self._modes:
            raise ValueError(f"Unknown mode: {mode_type}")

        mode_class = self._modes[mode_type]
        self._current_mode = mode_class(self.app)
        self._current_mode.on_activate()
        return self._current_mode

    def get_current_mode(self):
        return self._current_mode

    def handle_input(self, user_input: str) -> str:
        if not self._current_mode:
            return "No mode selected. Use /mode <name> to select a mode."

        suggested = self._current_mode.auto_switch(user_input)
        if suggested:
            mode_type = suggested.value
            if mode_type in self._modes:
                self.switch_mode(mode_type)
                return f"[Switched to {mode_type} mode]"

        return self._current_mode.handle_input(user_input)

"""
主模块单元测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from thera.__main__ import Thera, get_app
from thera.meta import ModeManager, Mode, ModeType, StorageManager


class TestThera:
    def test_default_storage_path(self):
        app = Thera()
        assert app.storage_path == Path.home() / "thera"

    def test_custom_storage_path(self):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        assert app.storage_path == Path("/tmp/test_thera")

    def test_init_creates_directories(self, tmp_path):
        app = Thera(storage_path=tmp_path)
        app.init()
        assert (tmp_path).exists()

    def test_init_sets_up_managers(self, tmp_path):
        app = Thera(storage_path=tmp_path)
        app.init()
        assert app._mode_manager is not None
        assert app._storage_manager is not None

    def test_mode_manager_property(self, tmp_path):
        app = Thera(storage_path=tmp_path)
        app.init()
        assert app.mode_manager is not None

    def test_storage_property(self, tmp_path):
        app = Thera(storage_path=tmp_path)
        app.init()
        assert app.storage is not None

    def test_switch_mode(self, tmp_path):
        app = Thera(storage_path=tmp_path)
        app.init()
        app.switch_mode("think")
        mode = app.mode_manager.get_current_mode()
        assert mode is not None
        assert mode.name == "think"

    def test_switch_mode_uninitialized(self):
        app = Thera()
        with pytest.raises(RuntimeError, match="not initialized"):
            app.switch_mode("chat")

    def test_property_uninitialized(self):
        app = Thera()
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = app.mode_manager


class TestModeManager:
    def test_register_mode(self, tmp_path):
        app = Thera(storage_path=tmp_path)
        app.init()

        class CustomMode(Mode):
            name = "custom"
            description = "Custom mode"

            def handle_input(self, user_input: str) -> str:
                return "custom"

            def on_activate(self):
                pass

            def on_deactivate(self):
                pass

        app.mode_manager.register("custom", CustomMode)
        assert "custom" in app.mode_manager._modes

    def test_switch_mode(self, tmp_path):
        app = Thera(storage_path=tmp_path)
        app.init()

        mode = app.mode_manager.switch_mode("think")
        assert mode.name == "think"

    def test_handle_input_no_mode(self):
        app = Thera()
        app.init()
        app.mode_manager._current_mode = None
        result = app.mode_manager.handle_input("hello")
        assert "No mode selected" in result

    def test_handle_input_with_mode(self, tmp_path):
        app = Thera(storage_path=tmp_path)
        app.init()
        app.mode_manager.switch_mode("think")
        result = app.mode_manager.handle_input("hello")
        assert "[Think] hello" in result


class TestStorageManager:
    def test_ensure_dirs(self, tmp_path):
        sm = StorageManager(tmp_path)
        sm.ensure_dirs()
        assert sm.base_path.exists()

    def test_get_data_dir(self, tmp_path):
        sm = StorageManager(tmp_path)
        path = sm.get_data_dir("test")
        assert path == tmp_path / "test"
        assert path.exists()

    def test_save_and_load_json(self, tmp_path):
        sm = StorageManager(tmp_path)
        sm.save_json("test", "data.json", {"key": "value"})
        data = sm.load_json("test", "data.json")
        assert data == {"key": "value"}

    def test_load_json_nonexistent(self, tmp_path):
        sm = StorageManager(tmp_path)
        data = sm.load_json("test", "nonexistent.json")
        assert data is None

    def test_save_and_load_yaml(self, tmp_path):
        sm = StorageManager(tmp_path)
        sm.save_yaml("test", "data.yaml", {"key": "value"})
        data = sm.load_yaml("test", "data.yaml")
        assert data == {"key": "value"}

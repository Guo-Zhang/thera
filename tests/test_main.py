"""
主模块单元测试 - ADAS 模型
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from thera.__main__ import Thera, get_app
from thera.meta import DomainManager, Domain, DomainType, StorageState


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
        assert tmp_path.exists()

    def test_init_sets_up_managers(self, tmp_path):
        app = Thera(storage_path=tmp_path)
        app.init()
        assert app._domain_manager is not None
        assert app._storage is not None

    def test_domain_manager_property(self, tmp_path):
        app = Thera(storage_path=tmp_path)
        app.init()
        assert app.domain_manager is not None

    def test_storage_property(self, tmp_path):
        app = Thera(storage_path=tmp_path)
        app.init()
        assert app.storage is not None

    def test_switch_activity(self, tmp_path):
        app = Thera(storage_path=tmp_path)
        app.init()
        app.switch_activity("think")
        activity = app.activity_manager.get_current_activity()
        assert activity is not None
        assert activity.name == "think"

    def test_switch_activity_uninitialized(self):
        app = Thera()
        with pytest.raises(RuntimeError, match="not initialized"):
            app.switch_activity("chat")

    def test_property_uninitialized(self):
        app = Thera()
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = app.domain_manager


class TestDomainManager:
    def test_register_domain(self, tmp_path):
        app = Thera(storage_path=tmp_path)
        app.init()

        class CustomDomain(Domain):
            name = "custom"
            description = "Custom domain"

            def handle_input(self, user_input: str) -> str:
                return "custom"

            def on_activate(self):
                pass

            def on_deactivate(self):
                pass

        app.domain_manager.register("custom", CustomDomain)
        assert "custom" in app.domain_manager._domains

    def test_switch_domain(self, tmp_path):
        app = Thera(storage_path=tmp_path)
        app.init()

        domain = app.domain_manager.switch_domain("think")
        assert domain.name == "think"

    def test_handle_input_no_domain(self):
        app = Thera()
        app.init()
        app.domain_manager._current_domain = None
        result = app.domain_manager.handle_input("hello")
        assert "No domain selected" in result

    def test_handle_input_with_domain(self, tmp_path):
        app = Thera(storage_path=tmp_path)
        app.init()
        app.domain_manager.switch_domain("think")
        result = app.domain_manager.handle_input("hello")
        assert "[Think] hello" in result


class TestStorageState:
    def test_ensure_dirs(self, tmp_path):
        sm = StorageState(tmp_path)
        sm.ensure_dirs()
        assert sm.base_path.exists()

    def test_get_data_dir(self, tmp_path):
        sm = StorageState(tmp_path)
        path = sm.get_data_dir("test")
        assert path == tmp_path / "test"
        assert path.exists()

    def test_save_and_load_json(self, tmp_path):
        sm = StorageState(tmp_path)
        sm.save_json("test", "data.json", {"key": "value"})
        data = sm.load_json("test", "data.json")
        assert data == {"key": "value"}

    def test_load_json_nonexistent(self, tmp_path):
        sm = StorageState(tmp_path)
        data = sm.load_json("test", "nonexistent.json")
        assert data is None

    def test_save_and_load_yaml(self, tmp_path):
        sm = StorageState(tmp_path)
        sm.save_yaml("test", "data.yaml", {"key": "value"})
        data = sm.load_yaml("test", "data.yaml")
        assert data == {"key": "value"}

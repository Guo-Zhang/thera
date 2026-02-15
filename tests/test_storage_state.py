"""
状态管理测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from thera.state.storage_state import StorageState


class TestStorageState:
    def test_base_path_validation(self):
        """测试基础路径验证"""
        base = Path("/tmp/thera")
        storage = StorageState(base)
        assert storage.base_path == base

    def test_save_inside_thera_folder(self):
        """测试在 thera 文件夹内保存"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "thera"
            base.mkdir()
            storage = StorageState(base)
            storage.save_json("test", "data.json", {"key": "value"})
            assert (base / "test" / "data.json").exists()

    def test_save_outside_thera_folder_fails(self):
        """测试跨文件夹保存失败"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "thera"
            base.mkdir()
            storage = StorageState(base)

            with pytest.raises((ValueError, FileNotFoundError)):
                storage.save_json("test", "../../../etc/passwd", {})

    def test_allowed_paths(self):
        """测试允许的路径"""
        base = Path("/home/user/thera")
        storage = StorageState(base)
        assert str(base) in storage.allowed_paths

"""
Base 模块单元测试
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from quanttide_apple.base import AppleAdapter, AppleResult, build_folder_tree


class TestAppleAdapter:
    """测试 AppleAdapter 抽象基类"""

    def test_abstract_class_cannot_instantiate(self):
        """测试无法直接实例化抽象类"""
        with pytest.raises(TypeError):
            AppleAdapter()

    def test_concrete_adapter(self):
        """测试具体适配器实现"""

        class TestAdapter(AppleAdapter):
            @property
            def app_name(self) -> str:
                return "TestApp"

            def fetch(self, **kwargs):
                return [{"id": 1, "name": "test"}]

        adapter = TestAdapter()
        assert adapter.app_name == "TestApp"
        assert adapter.fetch() == [{"id": 1, "name": "test"}]

    def test_run_shortcut(self):
        """测试 run_shortcut 方法"""

        class TestAdapter(AppleAdapter):
            @property
            def app_name(self) -> str:
                return "TestApp"

            def fetch(self, **kwargs):
                return []

        adapter = TestAdapter()
        with patch("quanttide_apple.base._run_shortcut") as mock_run:
            mock_run.return_value = "output"
            result = adapter.run_shortcut("TestShortcut")
            assert result == "output"
            mock_run.assert_called_once_with(
                "TestShortcut", input_data=None, timeout=120
            )

    def test_run_shortcut_with_input(self):
        """测试带输入的 run_shortcut"""

        class TestAdapter(AppleAdapter):
            @property
            def app_name(self) -> str:
                return "TestApp"

            def fetch(self, **kwargs):
                return []

        adapter = TestAdapter()
        with patch("quanttide_apple.base._run_shortcut") as mock_run:
            mock_run.return_value = "output"
            result = adapter.run_shortcut("TestShortcut", input_data="test", timeout=60)
            mock_run.assert_called_once_with(
                "TestShortcut", input_data="test", timeout=60
            )


class TestAppleResult:
    """测试 AppleResult 类"""

    def test_creation_with_data(self):
        """测试创建结果对象"""
        result = AppleResult([{"id": 1}])
        assert result.data == [{"id": 1}]
        assert result.meta == {}

    def test_creation_with_meta(self):
        """测试创建带元数据的结果"""
        result = AppleResult([{"id": 1}], {"total": 1})
        assert result.meta == {"total": 1}

    def test_count_list(self):
        """测试计数列表数据"""
        result = AppleResult([{"id": 1}, {"id": 2}, {"id": 3}])
        assert result.count == 3

    def test_count_single(self):
        """测试计数单个数据"""
        result = AppleResult({"id": 1})
        assert result.count == 1

    def test_count_empty(self):
        """测试计数空数据"""
        result = AppleResult(None)
        assert result.count == 0

    def test_to_dict(self):
        """测试转换为字典"""
        result = AppleResult([{"id": 1}], {"source": "test"})
        d = result.to_dict()
        assert d["data"] == [{"id": 1}]
        assert d["meta"] == {"source": "test"}


class TestBuildFolderTree:
    """测试 build_folder_tree 函数"""

    def test_empty_list(self):
        """测试空列表"""
        result = build_folder_tree([])
        assert result == []

    def test_single_folder(self):
        """测试单个文件夹"""
        folders = [{"id": "1", "name": "Folder 1", "parent_id": None}]
        result = build_folder_tree(folders)
        assert len(result) == 1
        assert result[0]["name"] == "Folder 1"
        assert result[0]["children"] == []

    def test_nested_folders(self):
        """测试嵌套文件夹"""
        folders = [
            {"id": "1", "name": "Root", "parent_id": None, "note_count": 10},
            {"id": "2", "name": "Child", "parent_id": "1", "note_count": 5},
        ]
        result = build_folder_tree(folders)
        assert len(result) == 1
        assert result[0]["name"] == "Root"
        assert len(result[0]["children"]) == 1
        assert result[0]["children"][0]["name"] == "Child"

    def test_multiple_roots(
        self,
    ):
        """测试多个根文件夹"""
        folders = [
            {"id": "1", "name": "Root 1", "parent_id": None},
            {"id": "2", "name": "Root 2", "parent_id": None},
        ]
        result = build_folder_tree(folders)
        assert len(result) == 2

    def test_missing_parent(self):
        """测试父级不存在的情况"""
        folders = [
            {"id": "1", "name": "Folder", "parent_id": "not_exist"},
        ]
        result = build_folder_tree(folders)
        assert len(result) == 1

    def test_deep_nesting(self):
        """测试深层嵌套"""
        folders = [
            {"id": "1", "name": "Level 1", "parent_id": None},
            {"id": "2", "name": "Level 2", "parent_id": "1"},
            {"id": "3", "name": "Level 3", "parent_id": "2"},
        ]
        result = build_folder_tree(folders)
        assert len(result) == 1
        level1 = result[0]
        assert level1["name"] == "Level 1"
        assert len(level1["children"]) == 1
        level2 = level1["children"][0]
        assert level2["name"] == "Level 2"
        assert len(level2["children"]) == 1
        level3 = level2["children"][0]
        assert level3["name"] == "Level 3"

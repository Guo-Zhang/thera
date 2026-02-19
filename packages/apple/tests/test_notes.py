"""
Notes 模块测试

支持通过 APPLE_USE_MOCK=true 切换到 mock 模式，默认使用真实 API。
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from quanttide_apple.notes import (
    NotesAdapter,
    get_notes_from_folder,
    get_note_names,
    export_notes,
)


class TestNotesAdapter:
    """测试 NotesAdapter 类"""

    def test_app_name(self):
        """测试 app_name 属性"""
        adapter = NotesAdapter()
        assert adapter.app_name == "Notes"

    def test_fetch_with_folder(self, is_mock):
        """测试获取指定文件夹的备忘录"""
        if is_mock:
            with patch(
                "quanttide_apple.notes.NotesAdapter._get_notes_from_folder"
            ) as mock_fetch:
                mock_fetch.return_value = [
                    {"title": "Note 1", "body": "Content 1"},
                    {"title": "Note 2", "body": "Content 2"},
                ]
                adapter = NotesAdapter()
                result = adapter.fetch(folder="思考")
                assert len(result) == 2
                assert result[0]["title"] == "Note 1"
        else:
            adapter = NotesAdapter()
            folders = adapter.get_folder_structure()
            if folders:
                result = adapter.fetch(folder=folders[0]["name"], limit=1)
                assert isinstance(result, list)

    def test_fetch_with_limit(self, is_mock):
        """测试限制数量获取"""
        if is_mock:
            with patch(
                "quanttide_apple.notes.NotesAdapter._get_notes_by_limit"
            ) as mock_fetch:
                mock_fetch.return_value = [{"title": "Note 1", "body": "Content 1"}]
                adapter = NotesAdapter()
                result = adapter.fetch(limit=10)
                assert len(result) == 1
        else:
            adapter = NotesAdapter()
            result = adapter.fetch(limit=3)
            assert isinstance(result, list)
            assert len(result) <= 3

    def test_fetch_default_folder(self, is_mock):
        """测试默认获取思考文件夹"""
        if is_mock:
            with patch(
                "quanttide_apple.notes.NotesAdapter._get_notes_from_folder"
            ) as mock_fetch:
                mock_fetch.return_value = [
                    {"title": "Test Note", "body": "Test Content"}
                ]
                adapter = NotesAdapter()
                result = adapter.fetch()
                assert len(result) == 1
        else:
            adapter = NotesAdapter()
            result = adapter.fetch(folder="思考", limit=1)
            assert isinstance(result, list)

    def test_get_folder_structure(self, is_mock):
        """测试获取文件夹结构"""
        if is_mock:
            with patch(
                "quanttide_apple.notes.NotesAdapter._get_folder_structure"
            ) as mock_fetch:
                mock_fetch.return_value = [
                    {"id": "1", "name": "Folder1", "parent_id": None, "note_count": 5},
                    {"id": "2", "name": "Folder2", "parent_id": None, "note_count": 10},
                ]
                adapter = NotesAdapter()
                result = adapter.get_folder_structure()
                assert len(result) == 2
        else:
            adapter = NotesAdapter()
            result = adapter.get_folder_structure()
            assert isinstance(result, list)

    def test_get_note_names(self, is_mock):
        """测试获取备忘录标题"""
        if is_mock:
            with patch("quanttide_apple.notes.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="Note 1, Note 2, Note 3",
                )
                adapter = NotesAdapter()
                result = adapter.get_note_names(limit=10)
                assert len(result) == 3
        else:
            adapter = NotesAdapter()
            result = adapter.get_note_names(limit=5)
            assert isinstance(result, list)

    def test_export_with_shortcut(self, is_mock):
        """测试通过 Shortcut 导出"""
        if is_mock:
            with patch("quanttide_apple.notes.NotesAdapter.run_shortcut") as mock_run:
                mock_run.return_value = '[{"title": "Note 1", "body": "Content 1"}]'
                adapter = NotesAdapter()
                with patch("pathlib.Path.mkdir"):
                    with patch("builtins.open", MagicMock()):
                        result = adapter.export(
                            folder="思考",
                            output_path=Path("/tmp/test.json"),
                            shortcut_name="GetAllNotes",
                        )
                        assert result["total_count"] == 1
        else:
            adapter = NotesAdapter()
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
                result = adapter.export(
                    folder="思考",
                    output_path=Path(f.name),
                )
                assert "total_count" in result


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_get_notes_from_folder(self, is_mock):
        """测试便捷函数 get_notes_from_folder"""
        if is_mock:
            with patch("quanttide_apple.notes.NotesAdapter.fetch") as mock_fetch:
                mock_fetch.return_value = [{"title": "Test"}]
                result = get_notes_from_folder("思考")
                assert result == [{"title": "Test"}]
        else:
            result = get_notes_from_folder("思考")
            assert isinstance(result, list)

    def test_get_note_names(self, is_mock):
        """测试便捷函数 get_note_names"""
        if is_mock:
            with patch(
                "quanttide_apple.notes.NotesAdapter.get_note_names"
            ) as mock_get_names:
                mock_get_names.return_value = ["Note 1", "Note 2"]
                result = get_note_names(limit=10)
                assert result == ["Note 1", "Note 2"]
        else:
            result = get_note_names(limit=5)
            assert isinstance(result, list)

    def test_export_notes(self, is_mock):
        """测试便捷函数 export_notes"""
        if is_mock:
            with patch("quanttide_apple.notes.NotesAdapter.export") as mock_export:
                mock_export.return_value = {"total_count": 1}
                with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
                    result = export_notes(folder="思考", output_path=Path(f.name))
                    assert result == {"total_count": 1}
        else:
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
                result = export_notes(folder="思考", output_path=Path(f.name))
                assert "total_count" in result


class TestNotesAdapterEdgeCases:
    """测试 NotesAdapter 边界情况"""

    def test_fetch_empty_result(self, is_mock):
        """测试空结果"""
        if is_mock:
            with patch("quanttide_apple.notes.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="")
                adapter = NotesAdapter()
                result = adapter.fetch(folder="EmptyFolder")
                assert result == []
        else:
            adapter = NotesAdapter()
            result = adapter.fetch(folder="NonExistentFolder12345")
            assert result == []

    def test_fetch_error(self, is_mock):
        """测试命令执行错误"""
        if is_mock:
            with patch("quanttide_apple.notes.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stdout="")
                adapter = NotesAdapter()
                result = adapter.fetch(folder="思考")
                assert result == []
        else:
            with patch("quanttide_apple.notes.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stdout="")
                adapter = NotesAdapter()
                result = adapter.fetch(folder="思考")
                assert result == []

    def test_fetch_exception(self, is_mock):
        """测试异常处理"""
        if is_mock:
            with patch("quanttide_apple.notes.subprocess.run") as mock_run:
                mock_run.side_effect = Exception("OSError")
                adapter = NotesAdapter()
                result = adapter.fetch(folder="思考")
                assert result == []
        else:
            with patch("quanttide_apple.notes.subprocess.run") as mock_run:
                mock_run.side_effect = Exception("OSError")
                adapter = NotesAdapter()
                result = adapter.fetch(folder="思考")
                assert result == []

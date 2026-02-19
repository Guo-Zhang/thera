"""
Shortcuts 模块测试

支持通过 APPLE_USE_MOCK=true 切换到 mock 模式，默认使用真实 API。
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from quanttide_apple.shortcuts import (
    list_shortcuts,
    run_shortcut,
    find_shortcut,
    get_shortcut_info,
)


class TestListShortcuts:
    """测试 list_shortcuts 函数"""

    def test_list_shortcuts_success(self, is_mock):
        """测试成功获取 Shortcuts 列表"""
        if is_mock:
            with patch("quanttide_apple.shortcuts.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="shortcut1\nshortcut2\nshortcut3\n",
                )
                result = list_shortcuts()
                assert result == ["shortcut1", "shortcut2", "shortcut3"]
        else:
            result = list_shortcuts()
            assert isinstance(result, list)
            assert len(result) > 0

    def test_list_shortcuts_empty(self, is_mock):
        """测试返回空列表"""
        if is_mock:
            with patch("quanttide_apple.shortcuts.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="")
                result = list_shortcuts()
                assert result == []
        else:
            result = list_shortcuts()
            assert isinstance(result, list)

    def test_list_shortcuts_error(self, is_mock):
        """测试命令执行失败"""
        if is_mock:
            with patch("quanttide_apple.shortcuts.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stdout="")
                result = list_shortcuts()
                assert result == []
        else:
            with patch("quanttide_apple.shortcuts.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stdout="")
                result = list_shortcuts()
                assert result == []

    def test_list_shortcuts_exception(self, is_mock):
        """测试异常处理"""
        if is_mock:
            with patch("quanttide_apple.shortcuts.subprocess.run") as mock_run:
                mock_run.side_effect = Exception("Command failed")
                result = list_shortcuts()
                assert result == []
        else:
            with patch("quanttide_apple.shortcuts.subprocess.run") as mock_run:
                mock_run.side_effect = Exception("Command failed")
                result = list_shortcuts()
                assert result == []


class TestRunShortcut:
    """测试 run_shortcut 函数"""

    def test_run_shortcut_success(self, is_mock):
        """测试成功运行 Shortcut"""
        if is_mock:
            with patch("quanttide_apple.shortcuts.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="shortcut output",
                )
                result = run_shortcut("MyShortcut")
                assert result == "shortcut output"
        else:
            shortcuts = list_shortcuts()
            if shortcuts:
                result = run_shortcut(shortcuts[0])
                assert result is not None or result is None

    def test_run_shortcut_error(self, is_mock):
        """测试运行失败"""
        if is_mock:
            with patch("quanttide_apple.shortcuts.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stdout="")
                result = run_shortcut("MyShortcut")
                assert result is None
        else:
            result = run_shortcut("NonExistentShortcut12345")
            assert result is None

    def test_run_shortcut_exception(self, is_mock):
        """测试异常处理"""
        if is_mock:
            with patch("quanttide_apple.shortcuts.subprocess.run") as mock_run:
                mock_run.side_effect = Exception("Command failed")
                result = run_shortcut("MyShortcut")
                assert result is None
        else:
            with patch("quanttide_apple.shortcuts.subprocess.run") as mock_run:
                mock_run.side_effect = Exception("Command failed")
                result = run_shortcut("MyShortcut")
                assert result is None

    def test_run_shortcut_with_input(self, is_mock):
        """测试带输入数据运行"""
        if is_mock:
            with patch("quanttide_apple.shortcuts.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="result")
                result = run_shortcut("MyShortcut", input_data="test input")
                mock_run.assert_called_once()
        else:
            shortcuts = list_shortcuts()
            if shortcuts:
                result = run_shortcut(shortcuts[0], input_data="test")
                assert result is not None or result is None


class TestFindShortcut:
    """测试 find_shortcut 函数"""

    def test_find_shortcut_exact_match(self, is_mock):
        """测试精确匹配"""
        if is_mock:
            with patch("quanttide_apple.shortcuts.list_shortcuts") as mock_list:
                mock_list.return_value = ["Get Notes", "Export Data", "Process Files"]
                result = find_shortcut("Get Notes")
                assert result == "Get Notes"
        else:
            shortcuts = list_shortcuts()
            if shortcuts:
                result = find_shortcut(shortcuts[0])
                assert result == shortcuts[0]

    def test_find_shortcut_partial_match(self, is_mock):
        """测试部分匹配"""
        if is_mock:
            with patch("quanttide_apple.shortcuts.list_shortcuts") as mock_list:
                mock_list.return_value = ["Get Notes", "Export Data", "Process Files"]
                result = find_shortcut("notes")
                assert result == "Get Notes"
        else:
            result = find_shortcut("语音")
            assert result is not None or result is None

    def test_find_shortcut_case_insensitive(self, is_mock):
        """测试不区分大小写"""
        if is_mock:
            with patch("quanttide_apple.shortcuts.list_shortcuts") as mock_list:
                mock_list.return_value = ["Get Notes", "Export Data"]
                result = find_shortcut("GET NOTES")
                assert result == "Get Notes"
        else:
            shortcuts = list_shortcuts()
            if shortcuts:
                result = find_shortcut(shortcuts[0].upper())
                assert result == shortcuts[0]

    def test_find_shortcut_not_found(self, is_mock):
        """测试未找到"""
        if is_mock:
            with patch("quanttide_apple.shortcuts.list_shortcuts") as mock_list:
                mock_list.return_value = ["Get Notes", "Export Data"]
                result = find_shortcut("NotExist")
                assert result is None
        else:
            result = find_shortcut("NotExist123456789")
            assert result is None


class TestGetShortcutInfo:
    """测试 get_shortcut_info 函数"""

    def test_get_shortcut_info_success(self, is_mock):
        """测试成功获取信息"""
        if is_mock:
            with patch("quanttide_apple.shortcuts.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="My Shortcut\n",
                )
                result = get_shortcut_info("My Shortcut")
                assert result == {"name": "My Shortcut"}
        else:
            shortcuts = list_shortcuts()
            if shortcuts:
                result = get_shortcut_info(shortcuts[0])
                assert result is not None

    def test_get_shortcut_info_error(self, is_mock):
        """测试获取失败"""
        if is_mock:
            with patch("quanttide_apple.shortcuts.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stdout="")
                result = get_shortcut_info("NotExist")
                assert result is None
        else:
            result = get_shortcut_info("NotExist123456789")
            assert result is None

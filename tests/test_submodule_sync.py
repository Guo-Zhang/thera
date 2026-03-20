"""测试子模块同步功能"""

import argparse
import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from thera import submodule_sync


class TestRunGit:
    """测试 run_git 函数"""

    def test_run_git_capture(self, tmp_path):
        """测试捕获输出的 git 命令"""
        result = submodule_sync.run_git(["status"], tmp_path)
        assert result is not None

    def test_run_git_no_capture(self, tmp_path, git_repo):
        """测试不捕获输出的 git 命令"""
        result = submodule_sync.run_git(["status"], git_repo, capture=False)
        assert result is True

    def test_run_git_invalid_command(self, tmp_path, git_repo):
        """测试无效命令"""
        result = submodule_sync.run_git(["invalid-command"], git_repo)
        assert result == ""  # 错误输出为空因为没有捕获 stderr


class TestGetSubmoduleStatus:
    """测试 get_submodule_status 函数"""

    def test_no_submodules(self, tmp_path, git_repo):
        """测试无子模块的情况"""
        result = submodule_sync.get_submodule_status(git_repo)
        assert result == []

    def test_empty_output(self, tmp_path):
        """测试空输出"""
        with patch("thera.submodule_sync.run_git") as mock:
            mock.return_value = ""
            result = submodule_sync.get_submodule_status(tmp_path)
            assert result == []

    def test_single_submodule_no_update(self, tmp_path):
        """测试单个子模块无更新"""
        with patch("thera.submodule_sync.run_git") as mock:
            mock.return_value = "abc1234 docs/archive\n"
            result = submodule_sync.get_submodule_status(tmp_path)
            assert len(result) == 1
            assert result[0]["path"] == "docs/archive"
            assert result[0]["local"] == "abc1234"
            assert result[0]["has_update"] is False

    def test_single_submodule_with_update(self, tmp_path):
        """测试单个子模块有更新"""
        with patch("thera.submodule_sync.run_git") as mock:
            mock.return_value = "+def5678 docs/tutorial\n"
            result = submodule_sync.get_submodule_status(tmp_path)
            assert len(result) == 1
            assert result[0]["has_update"] is True
            assert result[0]["local"] == "def5678"

    def test_multiple_submodules(self, tmp_path):
        """测试多个子模块"""
        with patch("thera.submodule_sync.run_git") as mock:
            output = "abc1234 docs/archive\ndef5678 docs/tutorial\n+ghi9012 src/thera\n"
            mock.return_value = output
            result = submodule_sync.get_submodule_status(tmp_path)
            assert len(result) == 3
            assert result[0]["path"] == "docs/archive"
            assert result[1]["path"] == "docs/tutorial"
            assert result[2]["has_update"] is True

    def test_with_empty_lines_in_output(self, tmp_path):
        """测试输出中包含空行（覆盖 continue 语句）"""
        with patch("thera.submodule_sync.run_git") as mock:
            output = "abc1234 docs/archive\n\ndef5678 docs/tutorial\n"
            mock.return_value = output
            result = submodule_sync.get_submodule_status(tmp_path)
            # 空行应该被跳过，不影响结果
            assert len(result) == 2


class TestSyncSubmodule:
    """测试 sync_submodule 函数"""

    def test_sync_success(self, tmp_path):
        """测试同步成功"""
        with patch("thera.submodule_sync.run_git") as mock:
            mock.return_value = True
            with patch("builtins.print"):
                result = submodule_sync.sync_submodule("docs/archive", tmp_path)
                assert result is True
                mock.assert_called_once()

    def test_sync_failure(self, tmp_path):
        """测试同步失败"""
        with patch("thera.submodule_sync.run_git") as mock:
            mock.return_value = False
            with patch("builtins.print"):
                result = submodule_sync.sync_submodule("docs/archive", tmp_path)
                assert result is False


class TestMain:
    """测试 main 函数"""

    def test_main_check_no_updates(self, tmp_path, git_repo):
        """测试检测无更新的情况"""
        with patch("thera.submodule_sync.get_submodule_status") as mock:
            mock.return_value = [
                {"path": "docs/archive", "local": "abc1234", "has_update": False}
            ]
            with patch("builtins.print"):
                args = argparse.Namespace(
                    check=True, sync=None, sync_all=False, repo=str(git_repo)
                )
                result = submodule_sync.main(args)
                assert result == 0

    def test_main_check_has_updates(self, tmp_path, git_repo):
        """测试检测到更新的情况"""
        with patch("thera.submodule_sync.get_submodule_status") as mock:
            mock.return_value = [
                {"path": "docs/archive", "local": "abc1234", "has_update": True}
            ]
            with patch("builtins.print"):
                args = argparse.Namespace(
                    check=True, sync=None, sync_all=False, repo=str(git_repo)
                )
                result = submodule_sync.main(args)
                assert result == 1

    def test_main_sync_single(self, tmp_path, git_repo):
        """测试同步单个子模块"""
        with patch("thera.submodule_sync.sync_submodule") as mock:
            mock.return_value = True
            with patch("builtins.print"):
                args = argparse.Namespace(
                    check=False, sync="docs/archive", sync_all=False, repo=str(git_repo)
                )
                result = submodule_sync.main(args)
                assert result == 0
                mock.assert_called_once()

    def test_main_sync_multiple(self, tmp_path, git_repo):
        """测试同步多个子模块"""
        with patch("thera.submodule_sync.sync_submodule") as mock:
            mock.return_value = True
            with patch("builtins.print"):
                args = argparse.Namespace(
                    check=False, sync="docs/archive,docs/tutorial", sync_all=False, repo=str(git_repo)
                )
                result = submodule_sync.main(args)
                assert result == 0
                assert mock.call_count == 2

    def test_main_sync_all(self, tmp_path, git_repo):
        """测试同步所有子模块"""
        with patch("thera.submodule_sync.run_git") as mock:
            mock.return_value = True
            with patch("builtins.print"):
                args = argparse.Namespace(
                    check=False, sync=None, sync_all=True, repo=str(git_repo)
                )
                result = submodule_sync.main(args)
                assert result == 0

    def test_main_no_args_shows_help(self, tmp_path, git_repo):
        """测试无参数时显示帮助"""
        with patch("builtins.print"):
            args = argparse.Namespace(
                check=False, sync=None, sync_all=False, repo=str(git_repo)
            )
            result = submodule_sync.main(args)
            assert result == 1

    def test_argparse_default_args(self, tmp_path, git_repo):
        """测试 argparse 默认参数路径（覆盖 59-64 行）"""
        with patch("builtins.print"):
            # Patch sys.argv to simulate running without arguments
            with patch("sys.argv", ["submodule_sync.py"]):
                result = submodule_sync.main()
                assert result == 1  # 显示帮助后退出

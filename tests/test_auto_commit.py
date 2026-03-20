"""测试自动提交推送功能"""

import argparse
import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from thera import auto_commit


class TestRunGit:
    """测试 run_git 函数"""

    def test_run_git_capture(self, git_repo):
        """测试捕获输出的 git 命令"""
        result = auto_commit.run_git(["status"], git_repo)
        assert len(result) == 3

    def test_run_git_no_capture(self, git_repo):
        """测试不捕获输出的 git 命令（覆盖 capture=False 分支）"""
        result = auto_commit.run_git(["status"], git_repo, capture=False)
        # capture=False 时返回 (None, None, returncode)
        assert result[0] is None
        assert result[1] is None
        assert result[2] == 0


class TestGetChangeType:
    """测试 get_change_type 函数"""

    def test_docs(self):
        """测试 docs 路径"""
        assert auto_commit.get_change_type("docs/README.md") == "docs"
        assert auto_commit.get_change_type("docs/tutorial/git.md") == "docs"

    def test_src(self):
        """测试 src 路径"""
        assert auto_commit.get_change_type("src/main.py") == "code"
        assert auto_commit.get_change_type("src/thera/cli.py") == "code"

    def test_config(self):
        """测试配置文件"""
        assert auto_commit.get_change_type(".gitmodules") == "config"
        assert auto_commit.get_change_type(".gitignore") == "config"

    def test_meta(self):
        """测试 meta 路径"""
        assert auto_commit.get_change_type("meta/journal/2026-03-20.md") == "meta"

    def test_root(self):
        """测试根目录文件"""
        assert auto_commit.get_change_type("README.md") == "root"
        assert auto_commit.get_change_type("CHANGELOG.md") == "root"
        assert auto_commit.get_change_type("AGENTS.md") == "root"


class TestGetRepoStatus:
    """测试 get_repo_status 函数"""

    def test_no_changes(self, tmp_path):
        """测试无变更"""
        with patch("thera.auto_commit.run_git") as mock:
            mock.return_value = ("", "", 0)
            result = auto_commit.get_repo_status(tmp_path)
            assert result == []

    def test_with_changes(self, tmp_path):
        """测试有变更"""
        with patch("thera.auto_commit.run_git") as mock:
            output = " M  docs/README.md\n?? new_file.txt\n"
            mock.return_value = (output, "", 0)
            result = auto_commit.get_repo_status(tmp_path)
            assert len(result) == 2
            assert result[0]["path"] == "docs/README.md"
            assert result[0]["type"] == "docs"

    def test_empty_output(self, tmp_path):
        """测试空输出"""
        with patch("thera.auto_commit.run_git") as mock:
            mock.return_value = ("", "", 0)
            result = auto_commit.get_repo_status(tmp_path)
            assert result == []

    def test_with_empty_lines(self, tmp_path):
        """测试输出包含空行（边界覆盖）"""
        with patch("thera.auto_commit.run_git") as mock:
            output = " M  docs/README.md\n\n?? new_file.txt\n"
            mock.return_value = (output, "", 0)
            result = auto_commit.get_repo_status(tmp_path)
            assert len(result) == 2


class TestGetSubmoduleStatus:
    """测试 get_submodule_status 函数"""

    def test_no_submodules(self, tmp_path):
        """测试无子模块"""
        with patch("thera.auto_commit.run_git") as mock:
            mock.return_value = ("", "", 0)
            result = auto_commit.get_submodule_status(tmp_path)
            assert result == []

    def test_with_submodules(self, tmp_path):
        """测试有子模块"""
        with patch("thera.auto_commit.run_git") as mock:
            output = "abc1234 docs/archive\ndef5678 docs/tutorial\n"
            mock.return_value = (output, "", 0)
            result = auto_commit.get_submodule_status(tmp_path)
            assert len(result) == 2
            assert "docs/archive" in result
            assert "docs/tutorial" in result

    def test_with_empty_lines(self, tmp_path):
        """测试输出包含空行（边界覆盖）"""
        with patch("thera.auto_commit.run_git") as mock:
            output = "abc1234 docs/archive\n\ndef5678 docs/tutorial\n"
            mock.return_value = (output, "", 0)
            result = auto_commit.get_submodule_status(tmp_path)
            assert len(result) == 2


class TestFormatChanges:
    """测试 format_changes 函数"""

    def test_no_changes(self):
        """测试无变更"""
        result = auto_commit.format_changes([])
        assert result == "No changes"

    def test_single_file(self):
        """测试单个文件"""
        changes = [{"path": "README.md", "type": "root", "status": "M"}]
        result = auto_commit.format_changes(changes)
        assert "[root] README.md" in result

    def test_multiple_files_same_type(self):
        """测试同类型多个文件"""
        changes = [
            {"path": "README.md", "type": "root", "status": "M"},
            {"path": "CHANGELOG.md", "type": "root", "status": "M"},
        ]
        result = auto_commit.format_changes(changes)
        assert "[root]" in result

    def test_files_truncation(self):
        """测试文件截断"""
        changes = [
            {"path": f"file{i}.txt", "type": "docs", "status": "M"}
            for i in range(6)
        ]
        result = auto_commit.format_changes(changes)
        assert "(+5 more)" in result


class TestDetectAllChanges:
    """测试 detect_all_changes 函数"""

    def test_no_changes(self, tmp_path):
        """测试无变更"""
        with patch("thera.auto_commit.get_submodule_status") as mock_sub:
            with patch("thera.auto_commit.get_repo_status") as mock_main:
                mock_sub.return_value = []
                mock_main.return_value = []
                result = auto_commit.detect_all_changes(tmp_path)
                assert result == {}

    def test_main_repo_changes(self, tmp_path):
        """测试主仓库变更"""
        with patch("thera.auto_commit.get_submodule_status") as mock_sub:
            with patch("thera.auto_commit.get_repo_status") as mock_main:
                mock_sub.return_value = []
                mock_main.return_value = [
                    {"path": "README.md", "type": "root", "status": "M"}
                ]
                result = auto_commit.detect_all_changes(tmp_path)
                assert "." in result

    def test_submodule_changes(self, tmp_path):
        """测试子模块变更"""
        with patch("thera.auto_commit.get_submodule_status") as mock_sub:
            with patch("thera.auto_commit.get_repo_status") as mock_main:
                mock_sub.return_value = ["docs/archive"]
                mock_main.return_value = []
                
                def side_effect(path):
                    if str(path).endswith("docs/archive"):
                        return [{"path": "README.md", "type": "docs", "status": "M"}]
                    return []
                
                mock_main.side_effect = side_effect
                result = auto_commit.detect_all_changes(tmp_path)
                assert "docs/archive" in result


class TestDisplayChanges:
    """测试 display_changes 函数"""

    def test_no_changes(self):
        """测试无变更"""
        with patch("builtins.print") as mock_print:
            result = auto_commit.display_changes({})
            assert result is False
            assert any("No changes detected" in str(c) for c in mock_print.call_args_list)

    def test_with_changes(self):
        """测试有变更"""
        changes = {
            ".": [{"path": "README.md", "type": "root", "status": "M"}]
        }
        with patch("builtins.print") as mock_print:
            result = auto_commit.display_changes(changes)
            assert result is True


class TestConfirmCommit:
    """测试 confirm_commit 函数"""

    def test_confirm_yes(self):
        """测试输入 y"""
        with patch("builtins.input", return_value="y"):
            with patch("builtins.print"):
                result = auto_commit.confirm_commit({})
                assert result is True

    def test_confirm_no(self):
        """测试输入 n"""
        with patch("builtins.input", return_value="n"):
            with patch("builtins.print"):
                result = auto_commit.confirm_commit({})
                assert result is False

    def test_confirm_quit(self):
        """测试输入 q"""
        with patch("builtins.input", return_value="q"):
            with patch("builtins.print"):
                result = auto_commit.confirm_commit({})
                assert result is False

    def test_confirm_empty(self):
        """测试空输入"""
        with patch("builtins.input", return_value=""):
            with patch("builtins.print"):
                result = auto_commit.confirm_commit({})
                assert result is False


class TestGenerateCommitMessage:
    """测试 generate_commit_message 函数"""

    def test_single_change(self):
        """测试单个变更"""
        changes = [{"path": "README.md", "type": "root", "status": "M"}]
        result = auto_commit.generate_commit_message(changes)
        assert "[root] README.md" in result

    def test_multiple_types(self):
        """测试多种类型"""
        changes = [
            {"path": "README.md", "type": "root", "status": "M"},
            {"path": "src/main.py", "type": "code", "status": "M"},
        ]
        result = auto_commit.generate_commit_message(changes)
        assert "[code]" in result
        assert "[root]" in result

    def test_many_files_truncation(self):
        """测试大量文件截断"""
        changes = [
            {"path": f"file{i}.txt", "type": "docs", "status": "M"}
            for i in range(8)
        ]
        result = auto_commit.generate_commit_message(changes)
        assert "(+3 more)" in result


class TestCommitAndPush:
    """测试 commit_and_push 函数"""

    def test_add_failure(self, tmp_path):
        """测试 git add 失败"""
        with patch("thera.git_ops.GitOps.run_git") as mock:
            mock.return_value = ("", "error", 1)
            with patch("builtins.print"):
                result = auto_commit.commit_and_push(tmp_path, ".", [])
                assert result == (False, "main", [])

    def test_nothing_to_commit(self, tmp_path):
        """测试无内容提交"""
        with patch("thera.git_ops.GitOps.run_git") as mock:
            def side_effect(args, capture=True):
                if args == ["add", "-A"]:
                    return ("", "", 0)
                elif args[0] == "commit":
                    return ("", "nothing to commit, working tree clean", 1)
                elif args[0] == "rev-parse":
                    return ("", "", 0)
                return ("", "", 0)
            mock.side_effect = side_effect
            with patch("builtins.print"):
                result = auto_commit.commit_and_push(tmp_path, ".", [])
                assert result == (True, "main", [])

    def test_commit_failure(self, tmp_path):
        """测试提交失败"""
        with patch("thera.git_ops.GitOps.run_git") as mock:
            def side_effect(args, capture=True):
                if args == ["add", "-A"]:
                    return ("", "", 0)
                elif args[0] == "commit":
                    return ("", "commit error", 1)
                return ("", "", 0)
            mock.side_effect = side_effect
            with patch("builtins.print"):
                result = auto_commit.commit_and_push(tmp_path, ".", [
                    {"path": "README.md", "type": "root", "status": "M"}
                ])
                assert result == (False, "main", [])

    def test_push_failure(self, tmp_path):
        """测试推送失败"""
        with patch("thera.git_ops.GitOps.run_git") as mock:
            def side_effect(args, capture=True):
                if args == ["add", "-A"]:
                    return ("", "", 0)
                elif args[0] == "commit":
                    return ("", "", 0)
                elif args[0] == "rev-parse":
                    return ("abc1234567890", "", 0)
                elif args[0] == "push":
                    return ("", "push error", 1)
                return ("", "", 0)
            mock.side_effect = side_effect
            with patch("builtins.print"):
                result = auto_commit.commit_and_push(tmp_path, ".", [
                    {"path": "README.md", "type": "root", "status": "M"}
                ])
                assert result == (False, "main", [])

    def test_success(self, tmp_path):
        """测试成功"""
        with patch("thera.git_ops.GitOps.run_git") as mock:
            def side_effect(args, capture=True):
                if args == ["add", "-A"]:
                    return ("", "", 0)
                elif args[0] == "commit":
                    return ("", "", 0)
                elif args[0] == "rev-parse":
                    return ("abc1234567890", "", 0)
                elif args[0] == "push":
                    return ("", "", 0)
                return ("", "", 0)
            mock.side_effect = side_effect
            with patch("builtins.print"):
                result = auto_commit.commit_and_push(tmp_path, ".", [
                    {"path": "README.md", "type": "root", "status": "M"}
                ])
                assert result[0] is True

    def test_success_submodule_with_sync_prefix(self, tmp_path):
        """测试子模块提交成功，验证 [sync] 前缀"""
        with patch("thera.git_ops.GitOps.run_git") as mock:
            def side_effect(args, capture=True):
                if args == ["add", "-A"]:
                    return ("", "", 0)
                elif args[0] == "commit" and args[1] == "-m":
                    assert "[sync]" in args[2]
                    return ("", "", 0)
                elif args[0] == "rev-parse":
                    return ("abc1234567890", "", 0)
                elif args[0] == "push":
                    return ("", "", 0)
                return ("", "", 0)
            mock.side_effect = side_effect
            with patch("builtins.print"):
                result = auto_commit.commit_and_push(tmp_path, "docs/archive", [
                    {"path": "README.md", "type": "docs", "status": "M"}
                ], is_main=True)
                assert result[0] is True

    def test_main_repo_label(self, tmp_path):
        """测试主仓库标签"""
        with patch("thera.git_ops.GitOps.run_git") as mock:
            def side_effect(args, capture=True):
                if args == ["add", "-A"]:
                    return ("", "error", 1)
                return ("", "", 0)
            mock.side_effect = side_effect
            with patch("builtins.print"):
                success, label, changes = auto_commit.commit_and_push(tmp_path, ".", [])
                assert label == "main"

    def test_submodule_label(self, tmp_path):
        """测试子模块标签"""
        with patch("thera.git_ops.GitOps.run_git") as mock:
            def side_effect(args, capture=True):
                if args == ["add", "-A"]:
                    return ("", "error", 1)
                return ("", "", 0)
            mock.side_effect = side_effect
            with patch("builtins.print"):
                success, label, changes = auto_commit.commit_and_push(tmp_path, "docs/archive", [])
                assert label == "docs/archive"


class TestAppendJournal:
    """测试 append_journal 函数"""

    def test_empty_results(self, tmp_path):
        """测试空结果"""
        with patch("builtins.print"):
            auto_commit.append_journal(tmp_path, [])
            assert True

    def test_append_to_journal(self, tmp_path):
        """测试追加日志"""
        journal_dir = tmp_path / "meta" / "journal"
        journal_dir.mkdir(parents=True)
        journal_file = journal_dir / f"{datetime.now().strftime('%Y-%m-%d')}.md"
        journal_file.write_text("# Journal\n")
        
        with patch("builtins.print"):
            auto_commit.append_journal(tmp_path, [
                (True, "main", [{"path": "README.md", "type": "root"}])
            ])
            
            content = journal_file.read_text()
            assert "OK" in content
            assert "main" in content

    def test_failed_status(self, tmp_path):
        """测试失败状态"""
        journal_dir = tmp_path / "meta" / "journal"
        journal_dir.mkdir(parents=True)
        
        with patch("builtins.print"):
            auto_commit.append_journal(tmp_path, [
                (False, "main", [{"path": "README.md", "type": "root"}])
            ])

    def test_skip_status(self, tmp_path):
        """测试跳过状态"""
        journal_dir = tmp_path / "meta" / "journal"
        journal_dir.mkdir(parents=True)
        
        with patch("builtins.print"):
            auto_commit.append_journal(tmp_path, [
                (True, "main", [])
            ])


class TestMain:
    """测试 main 函数"""

    def test_no_changes(self, tmp_path, git_repo):
        """测试无变更"""
        with patch("thera.auto_commit.detect_all_changes") as mock_detect:
            with patch("builtins.print"):
                mock_detect.return_value = {}
                args = argparse.Namespace(repo=str(git_repo), dry_run=False)
                result = auto_commit.main(args)
                assert result == 0

    def test_argparse_default_args(self, tmp_path, git_repo):
        """测试 argparse 默认参数路径（覆盖 243-246 行）"""
        with patch("thera.auto_commit.detect_all_changes") as mock_detect:
            with patch("builtins.print"):
                mock_detect.return_value = {}
                # Patch sys.argv to simulate running without arguments
                with patch("sys.argv", ["auto_commit.py"]):
                    result = auto_commit.main()
                    assert result == 0

    def test_dry_run(self, tmp_path, git_repo):
        """测试 dry-run 模式"""
        with patch("thera.auto_commit.detect_all_changes") as mock_detect:
            with patch("builtins.print"):
                mock_detect.return_value = {
                    ".": [{"path": "README.md", "type": "root", "status": "M"}]
                }
                args = argparse.Namespace(repo=str(git_repo), dry_run=True)
                result = auto_commit.main(args)
                assert result == 0

    def test_confirm_quit(self, tmp_path, git_repo):
        """测试确认退出"""
        with patch("thera.auto_commit.detect_all_changes") as mock_detect:
            with patch("builtins.print"):
                mock_detect.return_value = {
                    ".": [{"path": "README.md", "type": "root", "status": "M"}]
                }
                with patch("builtins.input", return_value="q"):
                    args = argparse.Namespace(repo=str(git_repo), dry_run=False)
                    result = auto_commit.main(args)
                    assert result == 0

    def test_confirm_no(self, tmp_path, git_repo):
        """测试确认拒绝"""
        with patch("thera.auto_commit.detect_all_changes") as mock_detect:
            with patch("builtins.print"):
                mock_detect.return_value = {
                    ".": [{"path": "README.md", "type": "root", "status": "M"}]
                }
                with patch("builtins.input", return_value="n"):
                    args = argparse.Namespace(repo=str(git_repo), dry_run=False)
                    result = auto_commit.main(args)
                    assert result == 0

    def test_success_with_submodules(self, tmp_path, git_repo):
        """测试有子模块的成功场景"""
        with patch("thera.auto_commit.detect_all_changes") as mock_detect:
            with patch("thera.auto_commit.commit_and_push") as mock_commit:
                with patch("thera.auto_commit.append_journal") as mock_journal:
                    with patch("builtins.print"):
                        mock_detect.return_value = {
                            "docs/archive": [{"path": "README.md", "type": "docs", "status": "M"}]
                        }
                        mock_commit.return_value = (True, "docs/archive", [])
                        
                        with patch("builtins.input", return_value="y"):
                            args = argparse.Namespace(repo=str(git_repo), dry_run=False)
                            result = auto_commit.main(args)
                            assert mock_commit.call_count == 1

    def test_failure_report(self, tmp_path, git_repo):
        """测试失败报告"""
        with patch("thera.auto_commit.detect_all_changes") as mock_detect:
            with patch("thera.auto_commit.commit_and_push") as mock_commit:
                with patch("thera.auto_commit.append_journal"):
                    with patch("builtins.print"):
                        mock_detect.return_value = {
                            ".": [{"path": "README.md", "type": "root", "status": "M"}]
                        }
                        mock_commit.return_value = (False, "main", [])
                        
                        with patch("builtins.input", return_value="y"):
                            args = argparse.Namespace(repo=str(git_repo), dry_run=False)
                            result = auto_commit.main(args)
                            assert result == 1

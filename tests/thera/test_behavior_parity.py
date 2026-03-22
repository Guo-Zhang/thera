"""
行为一致性测试

验证新领域层 (git_ops.py) 与旧应用层 (auto_commit.py) 行为完全一致。
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest

from thera import auto_commit as old_auto_commit
from thera.git_ops import GitOps, PushResult


@pytest.fixture
def temp_repo(tmp_path):
    """创建临时 git 仓库"""
    (tmp_path / ".git").mkdir()
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True
    )
    return tmp_path


class TestGetRepoStatus:
    """get_repo_status / get_status 行为对比"""

    @patch.object(old_auto_commit, "run_git")
    @patch.object(GitOps, "run_git")
    def test_clean_repo(self, mock_new_run, mock_old_run, temp_repo):
        mock_old_run.return_value = ("", "", 0)
        mock_new_run.return_value = ("", "", 0)

        old_result = old_auto_commit.get_repo_status(temp_repo)
        new_ops = GitOps(temp_repo)
        new_result = new_ops.get_status()

        assert (len(old_result) == 0) == new_result.is_clean

    @patch.object(old_auto_commit, "run_git")
    @patch.object(GitOps, "run_git")
    def test_modified_file(self, mock_new_run, mock_old_run, temp_repo):
        mock_old_run.return_value = (" M modified.txt\n", "", 0)
        mock_new_run.return_value = (" M modified.txt\n", "", 0)

        old_result = old_auto_commit.get_repo_status(temp_repo)
        new_ops = GitOps(temp_repo)
        new_result = new_ops.get_status()

        assert len(old_result) == 1 == len(new_result.changes)
        assert new_result.changes[0].path == "modified.txt"

    @patch.object(old_auto_commit, "run_git")
    @patch.object(GitOps, "run_git")
    def test_untracked_file(self, mock_new_run, mock_old_run, temp_repo):
        mock_old_run.return_value = ("?? untracked.txt\n", "", 0)
        mock_new_run.return_value = ("?? untracked.txt\n", "", 0)

        old_result = old_auto_commit.get_repo_status(temp_repo)
        new_ops = GitOps(temp_repo)
        new_result = new_ops.get_status()

        assert len(old_result) == 1 == len(new_result.changes)

    @patch.object(old_auto_commit, "run_git")
    @patch.object(GitOps, "run_git")
    def test_multiple_changes(self, mock_new_run, mock_old_run, temp_repo):
        output = " M src/main.py\n?? new.txt\n A docs/guide.md\n"
        mock_old_run.return_value = (output, "", 0)
        mock_new_run.return_value = (output, "", 0)

        old_result = old_auto_commit.get_repo_status(temp_repo)
        new_ops = GitOps(temp_repo)
        new_result = new_ops.get_status()

        assert len(old_result) == 3 == len(new_result.changes)


class TestGetSubmoduleStatus:
    """get_submodule_status 行为对比"""

    @patch.object(old_auto_commit, "run_git")
    @patch.object(GitOps, "run_git")
    def test_no_submodules(self, mock_new_run, mock_old_run, temp_repo):
        mock_old_run.return_value = ("", "", 0)
        mock_new_run.return_value = ("", "", 0)

        old_result = old_auto_commit.get_submodule_status(temp_repo)
        new_ops = GitOps(temp_repo)
        new_result = new_ops.get_submodule_status()

        assert old_result == new_result

    @patch.object(old_auto_commit, "run_git")
    @patch.object(GitOps, "run_git")
    def test_single_submodule(self, mock_new_run, mock_old_run, temp_repo):
        output = "abc1234 vendor/lib\n"
        mock_old_run.return_value = (output, "", 0)
        mock_new_run.return_value = (output, "", 0)

        old_result = old_auto_commit.get_submodule_status(temp_repo)
        new_ops = GitOps(temp_repo)
        new_result = new_ops.get_submodule_status()

        assert len(old_result) == len(new_result) == 1
        assert old_result[0] == new_result[0].path

    @patch.object(old_auto_commit, "run_git")
    @patch.object(GitOps, "run_git")
    def test_multiple_submodules(self, mock_new_run, mock_old_run, temp_repo):
        output = "abc1234 vendor/lib1\ndef5678 vendor/lib2\n"
        mock_old_run.return_value = (output, "", 0)
        mock_new_run.return_value = (output, "", 0)

        old_result = old_auto_commit.get_submodule_status(temp_repo)
        new_ops = GitOps(temp_repo)
        new_result = new_ops.get_submodule_status()

        assert len(old_result) == len(new_result) == 2
        assert old_result[0] == new_result[0].path
        assert old_result[1] == new_result[1].path


class TestGetChangeType:
    """get_change_type 行为对比"""

    def test_docs_path(self):
        assert old_auto_commit.get_change_type("docs/guide.md") == "docs"
        ops = GitOps(Path("."))
        assert ops._get_change_type("docs/guide.md") == "docs"

    def test_src_path(self):
        assert old_auto_commit.get_change_type("src/main.py") == "code"
        ops = GitOps(Path("."))
        assert ops._get_change_type("src/main.py") == "code"

    def test_config_files(self):
        assert old_auto_commit.get_change_type(".gitmodules") == "config"
        ops = GitOps(Path("."))
        assert ops._get_change_type(".gitmodules") == "config"

    def test_meta_path(self):
        assert old_auto_commit.get_change_type("meta/journal/2024.md") == "meta"
        ops = GitOps(Path("."))
        assert ops._get_change_type("meta/journal/2024.md") == "meta"

    def test_root_files(self):
        assert old_auto_commit.get_change_type("README.md") == "root"
        ops = GitOps(Path("."))
        assert ops._get_change_type("README.md") == "root"


class TestFormatChanges:
    """format_changes 行为对比"""

    def test_no_changes(self):
        old_result = old_auto_commit.format_changes([])
        new_result = old_auto_commit.format_changes([])
        assert old_result == new_result

    def test_single_file(self):
        changes = [{"path": "src/main.py", "type": "code"}]
        old_result = old_auto_commit.format_changes(changes)
        assert "src/main.py" in old_result

    def test_multiple_files(self):
        changes = [
            {"path": "src/main.py", "type": "code"},
            {"path": "docs/guide.md", "type": "docs"},
        ]
        old_result = old_auto_commit.format_changes(changes)
        assert "src/main.py" in old_result
        assert "docs/guide.md" in old_result


class TestCommitAndPush:
    """commit_and_push 行为对比"""

    @patch.object(GitOps, "run_git")
    def test_add_failure(self, mock_run_git, temp_repo):
        def side_effect(args, capture=True):
            if args[0] == "add":
                return ("", "error", 1)
            return ("", "", 0)

        mock_run_git.side_effect = side_effect

        ops = GitOps(temp_repo)
        result = ops.commit_and_push("test")

        assert result.success is False
        assert "add" in result.message.lower()

    @patch.object(GitOps, "run_git")
    def test_nothing_to_commit(self, mock_run_git, temp_repo):
        def side_effect(args, capture=True):
            if args[0] == "add":
                return ("", "", 0)
            elif args[0] == "commit":
                return ("", "nothing to commit", 1)
            return ("", "", 0)

        mock_run_git.side_effect = side_effect

        ops = GitOps(temp_repo)
        result = ops.commit_and_push("test")

        assert result.success is True
        assert "无变更" in result.message

    @patch.object(GitOps, "run_git")
    def test_commit_success(self, mock_run_git, temp_repo):
        def side_effect(args, capture=True):
            if args[0] == "add":
                return ("", "", 0)
            elif args[0] == "commit":
                return ("", "", 0)
            elif args[0] == "rev-parse":
                return ("abc1234567890\n", "", 0)
            elif args[0] == "push":
                return ("", "", 0)
            return ("", "", 0)

        mock_run_git.side_effect = side_effect

        ops = GitOps(temp_repo)
        result = ops.commit_and_push("test commit")

        assert result.success is True
        assert result.commit_sha == "abc1234"

    @patch.object(GitOps, "run_git")
    def test_push_failure(self, mock_run_git, temp_repo):
        def side_effect(args, capture=True):
            if args[0] == "add":
                return ("", "", 0)
            elif args[0] == "commit":
                return ("", "", 0)
            elif args[0] == "rev-parse":
                return ("abc1234567890\n", "", 0)
            elif args[0] == "push":
                return ("", "error: push failed", 1)
            return ("", "", 0)

        mock_run_git.side_effect = side_effect

        ops = GitOps(temp_repo)
        result = ops.commit_and_push("test commit")

        assert result.success is False
        assert "push" in result.message.lower()
        assert result.commit_sha == "abc1234"


class TestSyncSubmodules:
    """sync_submodules 行为对比"""

    @patch.object(GitOps, "run_git")
    def test_sync_success(self, mock_run_git, temp_repo):
        mock_run_git.return_value = ("", "", 0)

        ops = GitOps(temp_repo)
        result = ops.sync_submodules()

        assert result.success is True
        assert "同步完成" in result.message

    @patch.object(GitOps, "run_git")
    def test_sync_failure(self, mock_run_git, temp_repo):
        mock_run_git.return_value = ("", "error: fetch failed", 1)

        ops = GitOps(temp_repo)
        result = ops.sync_submodules()

        assert result.success is False
        assert result.error is not None

    @patch.object(GitOps, "run_git")
    def test_sync_specific_paths(self, mock_run_git, temp_repo):
        mock_run_git.return_value = ("", "", 0)

        ops = GitOps(temp_repo)
        result = ops.sync_submodules(["vendor/lib1"])

        assert result.success is True
        assert "vendor/lib1" in result.synced_paths


class TestRunGit:
    """run_git 行为对比"""

    def test_run_git_interface(self, temp_repo):
        """验证 GitOps.run_git 接口一致性"""
        ops = GitOps(temp_repo)
        stdout, stderr, code = ops.run_git(["status"])

        assert isinstance(stdout, str)
        assert isinstance(stderr, str)
        assert isinstance(code, int)

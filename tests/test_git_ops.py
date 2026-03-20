"""
GitOps 层测试

测试 git_ops.py 中定义的 Git 操作封装。
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thera.git_ops import (
    ChangeType,
    ConsistencyResult,
    FileChange,
    GitOps,
    OperationResult,
    PushResult,
    RepoStatus,
    SubmoduleInfo,
    SyncResult,
)


@pytest.fixture
def git_ops(tmp_path):
    """创建 GitOps 实例"""
    return GitOps(tmp_path)


@pytest.fixture
def mock_repo(tmp_path):
    """创建模拟的 git 仓库"""
    (tmp_path / ".git").mkdir()
    return tmp_path


class TestChangeType:
    """ChangeType 枚举测试"""

    def test_all_change_types_defined(self):
        assert ChangeType.NEW is not None
        assert ChangeType.MODIFIED is not None
        assert ChangeType.DELETED is not None
        assert ChangeType.UNTRACKED is not None

    def test_change_type_count(self):
        assert len(ChangeType) == 4


class TestFileChange:
    """FileChange 数据类测试"""

    def test_file_change_creation(self):
        change = FileChange(
            path="src/main.py",
            change_type=ChangeType.MODIFIED,
            type_prefix="code",
        )
        assert change.path == "src/main.py"
        assert change.change_type == ChangeType.MODIFIED
        assert change.type_prefix == "code"


class TestRepoStatus:
    """RepoStatus 数据类测试"""

    def test_clean_status(self):
        status = RepoStatus(is_clean=True, changes=[])
        assert status.is_clean is True
        assert status.changes == []

    def test_dirty_status(self):
        changes = [
            FileChange("src/main.py", ChangeType.MODIFIED, "code"),
        ]
        status = RepoStatus(is_clean=False, changes=changes)
        assert status.is_clean is False
        assert len(status.changes) == 1


class TestSubmoduleInfo:
    """SubmoduleInfo 数据类测试"""

    def test_submodule_info_creation(self):
        info = SubmoduleInfo(
            path="vendor/lib",
            local_commit="abc1234",
            is_behind=True,
            is_detached=False,
        )
        assert info.path == "vendor/lib"
        assert info.local_commit == "abc1234"
        assert info.is_behind is True
        assert info.is_detached is False


class TestOperationResult:
    """OperationResult 基类测试"""

    def test_operation_result_success(self):
        result = OperationResult(success=True, message="OK")
        assert result.success is True
        assert result.message == "OK"
        assert result.error is None

    def test_operation_result_failure(self):
        result = OperationResult(
            success=False, message="FAIL", error="some error"
        )
        assert result.success is False
        assert result.error == "some error"


class TestConsistencyResult:
    """ConsistencyResult 测试"""

    def test_consistent_result(self):
        result = ConsistencyResult(
            success=True,
            is_consistent=True,
            message="一致",
        )
        assert result.success is True
        assert result.is_consistent is True

    def test_inconsistent_result(self):
        result = ConsistencyResult(
            success=False,
            is_consistent=False,
            message="不一致",
            missing_paths=["path1", "path2"],
        )
        assert result.success is False
        assert result.is_consistent is False
        assert result.missing_paths == ["path1", "path2"]


class TestSyncResult:
    """SyncResult 测试"""

    def test_sync_success(self):
        result = SyncResult(
            success=True,
            message="同步完成",
            synced_paths=["path1", "path2"],
        )
        assert result.success is True
        assert result.synced_paths == ["path1", "path2"]

    def test_sync_failure(self):
        result = SyncResult(
            success=False,
            message="同步失败",
            error="git error",
        )
        assert result.success is False
        assert result.error == "git error"


class TestPushResult:
    """PushResult 测试"""

    def test_push_success(self):
        result = PushResult(
            success=True,
            message="推送成功",
            commit_sha="abc1234",
        )
        assert result.success is True
        assert result.commit_sha == "abc1234"

    def test_push_failure(self):
        result = PushResult(
            success=False,
            message="推送失败",
            error="network error",
            commit_sha="abc1234",
        )
        assert result.success is False
        assert result.error == "network error"


class TestGitOps:
    """GitOps 类测试"""

    def test_init(self, git_ops):
        assert git_ops.repo_root == git_ops.repo_root

    def test_get_change_type_docs(self, git_ops):
        assert git_ops._get_change_type("docs/guide.md") == "docs"

    def test_get_change_type_src(self, git_ops):
        assert git_ops._get_change_type("src/main.py") == "code"

    def test_get_change_type_gitmodules(self, git_ops):
        assert git_ops._get_change_type(".gitmodules") == "config"

    def test_get_change_type_meta(self, git_ops):
        assert git_ops._get_change_type("meta/journal/2024-01-01.md") == "meta"

    def test_get_change_type_root(self, git_ops):
        assert git_ops._get_change_type("README.md") == "root"


class TestGitOpsGetStatus:
    """GitOps.get_status() 测试"""

    @patch.object(GitOps, "run_git")
    def test_clean_repo(self, mock_run_git, git_ops):
        mock_run_git.return_value = ("", "", 0)

        status = git_ops.get_status()

        assert status.is_clean is True
        assert status.changes == []

    @patch.object(GitOps, "run_git")
    def test_untracked_file(self, mock_run_git, git_ops):
        mock_run_git.return_value = ("?? untracked.txt\n", "", 0)

        status = git_ops.get_status()

        assert status.is_clean is False
        assert len(status.changes) == 1
        assert status.changes[0].path == "untracked.txt"
        assert status.changes[0].change_type == ChangeType.UNTRACKED

    @patch.object(GitOps, "run_git")
    def test_modified_file(self, mock_run_git, git_ops):
        mock_run_git.return_value = (" M modified.txt\n", "", 0)

        status = git_ops.get_status()

        assert status.is_clean is False
        assert status.changes[0].change_type == ChangeType.MODIFIED

    @patch.object(GitOps, "run_git")
    def test_new_file(self, mock_run_git, git_ops):
        mock_run_git.return_value = ("A  new.txt\n", "", 0)

        status = git_ops.get_status()

        assert status.changes[0].change_type == ChangeType.NEW

    @patch.object(GitOps, "run_git")
    def test_deleted_file(self, mock_run_git, git_ops):
        mock_run_git.return_value = ("D  deleted.txt\n", "", 0)

        status = git_ops.get_status()

        assert status.changes[0].change_type == ChangeType.DELETED

    @patch.object(GitOps, "run_git")
    def test_multiple_changes(self, mock_run_git, git_ops):
        mock_run_git.return_value = (
            " M src/main.py\n?? new.txt\n A docs/guide.md\n",
            "",
            0,
        )

        status = git_ops.get_status()

        assert len(status.changes) == 3


class TestGitOpsSubmoduleStatus:
    """GitOps.get_submodule_status() 测试"""

    @patch.object(GitOps, "run_git")
    def test_no_submodules(self, mock_run_git, git_ops):
        mock_run_git.return_value = ("", "", 0)

        result = git_ops.get_submodule_status()

        assert result == []

    @patch.object(GitOps, "run_git")
    def test_single_submodule(self, mock_run_git, git_ops):
        mock_run_git.return_value = ("abc1234 vendor/lib\n", "", 0)

        result = git_ops.get_submodule_status()

        assert len(result) == 1
        assert result[0].path == "vendor/lib"
        assert result[0].local_commit == "abc1234"
        assert result[0].is_behind is False

    @patch.object(GitOps, "run_git")
    def test_submodule_behind(self, mock_run_git, git_ops):
        mock_run_git.return_value = ("+def5678 vendor/lib\n", "", 0)

        result = git_ops.get_submodule_status()

        assert result[0].is_behind is True
        assert result[0].local_commit == "def5678"

    @patch.object(GitOps, "run_git")
    def test_submodule_detached(self, mock_run_git, git_ops):
        mock_run_git.return_value = ("u1234567 vendor/lib\n", "", 0)

        result = git_ops.get_submodule_status()

        assert result[0].is_detached is True

    @patch.object(GitOps, "run_git")
    def test_multiple_submodules(self, mock_run_git, git_ops):
        mock_run_git.return_value = (
            "abc1234 vendor/lib1\ndef5678 vendor/lib2\n",
            "",
            0,
        )

        result = git_ops.get_submodule_status()

        assert len(result) == 2
        assert result[0].path == "vendor/lib1"
        assert result[1].path == "vendor/lib2"


class TestGitOpsCheckConsistency:
    """GitOps.check_consistency() 测试"""

    @patch.object(GitOps, "run_git")
    def test_yaml_not_found(self, mock_run_git, git_ops, tmp_path):
        result = git_ops.check_consistency(Path("missing.yaml"))

        assert result.success is False
        assert result.is_consistent is False

    @patch.object(GitOps, "run_git")
    def test_consistent_paths(self, mock_run_git, git_ops, tmp_path):
        yaml_path = tmp_path / "submodules.yaml"
        yaml_path.write_text(
            "submodules:\n  - path: vendor/lib1\n    url: git://example.com/lib1\n"
        )
        (tmp_path / "vendor" / "lib1").mkdir(parents=True)

        def config_side_effect(args):
            if "config" in args[0]:
                return "submodule.vendor/lib1.path vendor/lib1\n", "", 0
            return "", "", 0

        mock_run_git.side_effect = config_side_effect

        result = git_ops.check_consistency(yaml_path)

        assert result.success is True
        assert result.is_consistent is True

    @patch.object(GitOps, "run_git")
    def test_missing_in_yaml(self, mock_run_git, git_ops, tmp_path):
        yaml_path = tmp_path / "submodules.yaml"
        yaml_path.write_text(
            "submodules:\n  - path: vendor/lib1\n    url: git://example.com/lib1\n"
        )

        def config_side_effect(args):
            if "config" in args[0]:
                return (
                    "submodule.vendor/lib1.path vendor/lib1\nsubmodule.vendor/lib2.path vendor/lib2\n",
                    "",
                    0,
                )
            return "", "", 0

        mock_run_git.side_effect = config_side_effect

        result = git_ops.check_consistency(yaml_path)

        assert result.success is False
        assert result.is_consistent is False
        assert "vendor/lib2" in result.missing_paths


class TestGitOpsSyncSubmodules:
    """GitOps.sync_submodules() 测试"""

    @patch.object(GitOps, "run_git")
    def test_sync_success(self, mock_run_git, git_ops):
        mock_run_git.return_value = ("", "", 0)

        result = git_ops.sync_submodules()

        assert result.success is True
        assert result.message == "同步完成"

    @patch.object(GitOps, "run_git")
    def test_sync_specific_paths(self, mock_run_git, git_ops):
        mock_run_git.return_value = ("", "", 0)

        result = git_ops.sync_submodules(["vendor/lib1"])

        assert result.success is True
        assert result.synced_paths == ["vendor/lib1"]

    @patch.object(GitOps, "run_git")
    def test_sync_failure(self, mock_run_git, git_ops):
        mock_run_git.return_value = ("", "error: fetch failed", 1)

        result = git_ops.sync_submodules()

        assert result.success is False
        assert result.error == "error: fetch failed"


class TestGitOpsCommitAndPush:
    """GitOps.commit_and_push() 测试"""

    @patch.object(GitOps, "run_git")
    def test_commit_and_push_success(self, mock_run_git, git_ops):
        def side_effect(args):
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

        result = git_ops.commit_and_push("test commit")

        assert result.success is True
        assert result.commit_sha == "abc1234"

    @patch.object(GitOps, "run_git")
    def test_add_failure(self, mock_run_git, git_ops):
        mock_run_git.return_value = ("", "error: add failed", 1)

        result = git_ops.commit_and_push("test commit")

        assert result.success is False
        assert "add 失败" in result.message

    @patch.object(GitOps, "run_git")
    def test_commit_failure(self, mock_run_git, git_ops):
        def side_effect(args):
            if args[0] == "add":
                return ("", "", 0)
            elif args[0] == "commit":
                return ("", "error: commit failed", 1)
            return ("", "", 0)

        mock_run_git.side_effect = side_effect

        result = git_ops.commit_and_push("test commit")

        assert result.success is False
        assert "commit 失败" in result.message

    @patch.object(GitOps, "run_git")
    def test_nothing_to_commit(self, mock_run_git, git_ops):
        def side_effect(args):
            if args[0] == "add":
                return ("", "", 0)
            elif args[0] == "commit":
                return ("", "nothing to commit, working tree clean", 1)
            return ("", "", 0)

        mock_run_git.side_effect = side_effect

        result = git_ops.commit_and_push("test commit")

        assert result.success is True
        assert result.message == "无变更"

    @patch.object(GitOps, "run_git")
    def test_push_failure(self, mock_run_git, git_ops):
        def side_effect(args):
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

        result = git_ops.commit_and_push("test commit")

        assert result.success is False
        assert "push 失败" in result.message
        assert result.commit_sha == "abc1234"


class TestGitOpsRunGit:
    """GitOps.run_git() 测试"""

    def test_run_git_success(self, git_ops):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="output", stderr="", returncode=0
            )

            stdout, stderr, code = git_ops.run_git(["status"])

            assert stdout == "output"
            assert code == 0

    def test_run_git_failure(self, git_ops):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="", stderr="error", returncode=1
            )

            stdout, stderr, code = git_ops.run_git(["status"])

            assert code == 1
            assert stderr == "error"

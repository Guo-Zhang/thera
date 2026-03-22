"""
refresh 命令测试
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thera.git_ops import SubmoduleInfo
from thera.refresh import RefreshResult, get_submodule_updates, refresh


@pytest.fixture
def ops_mock():
    """创建 GitOps mock"""
    return MagicMock()


@pytest.fixture
def clean_submodules():
    """模拟所有子模块都是干净的"""
    with patch("thera.refresh._get_dirty_submodules", return_value=[]):
        yield


class TestRefresh:
    """refresh 函数测试"""

    def test_refresh_no_updates_no_changes(self, ops_mock, clean_submodules):
        """测试无更新无变更"""
        ops_mock.get_submodule_status.return_value = []
        ops_mock.get_status.return_value = MagicMock(is_clean=True)

        with patch("thera.refresh.GitOps", return_value=ops_mock):
            result = refresh(Path("."))

        assert result.success is True
        assert result.message == "已是最新"
        assert result.updated_submodules == []

    def test_refresh_with_submodule_updates(self, ops_mock, clean_submodules):
        """测试有子模块更新"""
        ops_mock.get_submodule_status.return_value = [
            SubmoduleInfo(
                path="docs/archive",
                local_commit="abc",
                is_behind=True,
                is_detached=False,
            ),
        ]
        ops_mock.get_status.return_value = MagicMock(is_clean=True)
        ops_mock.sync_submodules.return_value = MagicMock(success=True)

        with patch("thera.refresh.GitOps", return_value=ops_mock):
            result = refresh(Path("."))

        assert result.success is True
        assert result.message == "子模块已更新"
        assert result.updated_submodules == ["docs/archive"]

    def test_refresh_with_changes_to_commit(self, ops_mock, clean_submodules):
        """测试有变更需要提交"""
        ops_mock.get_submodule_status.return_value = []
        ops_mock.get_status.return_value = MagicMock(
            is_clean=False, changes=[MagicMock(), MagicMock()]
        )
        ops_mock.commit_and_push.return_value = MagicMock(
            success=True, commit_sha="abc1234"
        )

        with patch("thera.refresh.GitOps", return_value=ops_mock):
            result = refresh(Path("."))

        assert result.success is True
        assert result.commit_sha == "abc1234"
        ops_mock.commit_and_push.assert_called_once()

    def test_refresh_dry_run(self, ops_mock, clean_submodules):
        """测试预览模式"""
        ops_mock.get_submodule_status.return_value = [
            SubmoduleInfo(
                path="docs/archive",
                local_commit="abc",
                is_behind=True,
                is_detached=False,
            ),
        ]
        ops_mock.get_status.return_value = MagicMock(
            is_clean=False, changes=[MagicMock()]
        )

        with patch("thera.refresh.GitOps", return_value=ops_mock):
            result = refresh(Path("."), dry_run=True)

        assert result.success is True
        assert result.dry_run is True
        assert "将提交" in result.message
        ops_mock.sync_submodules.assert_not_called()
        ops_mock.commit_and_push.assert_not_called()

    def test_refresh_commit_failure(self, ops_mock, clean_submodules):
        """测试提交失败"""
        ops_mock.get_submodule_status.return_value = []
        ops_mock.get_status.return_value = MagicMock(
            is_clean=False, changes=[MagicMock()]
        )
        ops_mock.commit_and_push.return_value = MagicMock(
            success=False, error="push rejected"
        )

        with patch("thera.refresh.GitOps", return_value=ops_mock):
            result = refresh(Path("."))

        assert result.success is False
        assert result.error == "push rejected"

    def test_refresh_dirty_submodule(self):
        """测试子模块有内部未提交变更"""
        with patch(
            "thera.refresh._get_dirty_submodules", return_value=["docs/journal"]
        ):
            result = refresh(Path("."))

        assert result.success is False
        assert "子模块有未提交的变更" in result.message
        assert result.error is not None
        assert "docs/journal" in result.error


class TestGetSubmoduleUpdates:
    """get_submodule_updates 测试"""

    def test_no_updates(self, ops_mock):
        """测试无更新"""
        ops_mock.get_submodule_status.return_value = [
            SubmoduleInfo(
                path="docs/archive",
                local_commit="abc",
                is_behind=False,
                is_detached=False,
            ),
        ]

        with patch("thera.refresh.GitOps", return_value=ops_mock):
            updates = get_submodule_updates(Path("."))

        assert len(updates) == 0

    def test_with_updates(self, ops_mock):
        """测试有更新"""
        ops_mock.get_submodule_status.return_value = [
            SubmoduleInfo(
                path="docs/archive",
                local_commit="abc",
                is_behind=True,
                is_detached=False,
            ),
            SubmoduleInfo(
                path="src/thera", local_commit="def", is_behind=False, is_detached=False
            ),
        ]

        with patch("thera.refresh.GitOps", return_value=ops_mock):
            updates = get_submodule_updates(Path("."))

        assert len(updates) == 1
        assert updates[0].path == "docs/archive"

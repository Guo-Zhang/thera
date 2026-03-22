"""
refresh 命令测试
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thera.git_ops import SubmoduleInfo
from thera.refresh import (
    RefreshResult,
    _fetch_submodules,
    _get_dirty_submodules,
    _get_submodules_behind_remote,
    get_submodule_updates,
    refresh,
)


class TestRefresh:
    """refresh 函数测试"""

    def test_refresh_no_updates_no_changes(self):
        """测试无更新无变更"""
        with patch("thera.refresh._get_dirty_submodules", return_value=[]):
            with patch("thera.refresh._fetch_submodules"):
                with patch(
                    "thera.refresh._get_submodules_behind_remote", return_value=[]
                ):
                    with patch("thera.refresh.GitOps") as mock_ops_class:
                        mock_ops = MagicMock()
                        mock_ops.get_status.return_value = MagicMock(is_clean=True)
                        mock_ops_class.return_value = mock_ops
                        result = refresh(Path("."))

        assert result.success is True
        assert result.message == "已是最新"
        assert result.updated_submodules == []

    def test_refresh_with_submodule_updates(self):
        """测试有子模块更新"""
        submodule = SubmoduleInfo(
            path="docs/archive",
            local_commit="abc1234",
            is_behind=True,
            is_detached=False,
        )

        with patch("thera.refresh._get_dirty_submodules", return_value=[]):
            with patch("thera.refresh._fetch_submodules"):
                with patch(
                    "thera.refresh._get_submodules_behind_remote",
                    return_value=[submodule],
                ):
                    with patch("thera.refresh.GitOps") as mock_ops_class:
                        mock_ops = MagicMock()
                        mock_ops.get_status.return_value = MagicMock(is_clean=True)
                        mock_ops.sync_submodules.return_value = MagicMock(success=True)
                        mock_ops_class.return_value = mock_ops
                        result = refresh(Path("."))

        assert result.success is True
        assert result.message == "子模块已更新"
        assert result.updated_submodules == ["docs/archive"]

    def test_refresh_with_changes_to_commit(self):
        """测试有变更需要提交"""
        with patch("thera.refresh._get_dirty_submodules", return_value=[]):
            with patch("thera.refresh._fetch_submodules"):
                with patch(
                    "thera.refresh._get_submodules_behind_remote", return_value=[]
                ):
                    with patch("thera.refresh.GitOps") as mock_ops_class:
                        mock_ops = MagicMock()
                        mock_ops.get_status.return_value = MagicMock(
                            is_clean=False, changes=[MagicMock(), MagicMock()]
                        )
                        mock_ops.commit_and_push.return_value = MagicMock(
                            success=True, commit_sha="abc1234"
                        )
                        mock_ops_class.return_value = mock_ops
                        result = refresh(Path("."))

        assert result.success is True
        assert result.commit_sha == "abc1234"
        mock_ops.commit_and_push.assert_called_once()

    def test_refresh_dry_run(self):
        """测试预览模式"""
        submodule = SubmoduleInfo(
            path="docs/archive",
            local_commit="abc1234",
            is_behind=True,
            is_detached=False,
        )

        with patch("thera.refresh._get_dirty_submodules", return_value=[]):
            with patch("thera.refresh._fetch_submodules"):
                with patch(
                    "thera.refresh._get_submodules_behind_remote",
                    return_value=[submodule],
                ):
                    with patch("thera.refresh.GitOps") as mock_ops_class:
                        mock_ops = MagicMock()
                        mock_ops.get_status.return_value = MagicMock(
                            is_clean=False, changes=[MagicMock()]
                        )
                        mock_ops_class.return_value = mock_ops
                        result = refresh(Path("."), dry_run=True)

        assert result.success is True
        assert result.dry_run is True
        assert "将提交" in result.message

    def test_refresh_commit_failure(self):
        """测试提交失败"""
        with patch("thera.refresh._get_dirty_submodules", return_value=[]):
            with patch("thera.refresh._fetch_submodules"):
                with patch(
                    "thera.refresh._get_submodules_behind_remote", return_value=[]
                ):
                    with patch("thera.refresh.GitOps") as mock_ops_class:
                        mock_ops = MagicMock()
                        mock_ops.get_status.return_value = MagicMock(
                            is_clean=False, changes=[MagicMock()]
                        )
                        mock_ops.commit_and_push.return_value = MagicMock(
                            success=False, error="push rejected"
                        )
                        mock_ops_class.return_value = mock_ops
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


class TestFetchSubmodules:
    """_fetch_submodules 测试"""

    def test_fetch_skips_nonexistent(self, tmp_path):
        """测试跳过不存在的子模块"""
        with patch("thera.refresh.subprocess.run") as mock_run:
            _fetch_submodules(tmp_path)
            mock_run.assert_not_called()


class TestGetSubmodulesBehindRemote:
    """_get_submodules_behind_remote 测试"""

    def test_skips_nonexistent(self, tmp_path):
        """测试跳过不存在的子模块"""
        with patch("thera.refresh.subprocess.run") as mock_run:
            result = _get_submodules_behind_remote(tmp_path)
            assert result == []
            mock_run.assert_not_called()

"""
Workflow 层测试

测试 workflow.py 中定义的工作流引擎。
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thera.fsm import ErrorState, Event, RepoState
from thera.git_ops import ConsistencyResult, PushResult, SyncResult
from thera.workflow import (
    AutoStrategy,
    ConvergenceStrategy,
    HybridStrategy,
    ManualStrategy,
    WorkflowEngine,
    WorkflowResult,
)


@pytest.fixture
def workflow_engine(tmp_path):
    """创建 WorkflowEngine 实例"""
    return WorkflowEngine(tmp_path)


@pytest.fixture
def workflow_engine_with_mock(tmp_path):
    """创建带有 mock GitOps 的 WorkflowEngine"""
    engine = WorkflowEngine(tmp_path)
    engine.git_ops = MagicMock()
    return engine


class TestConvergenceStrategy:
    """ConvergenceStrategy 测试"""

    def test_auto_strategy_always_reconciles(self):
        strategy = AutoStrategy()
        assert strategy.should_reconcile("lib1", True) is True
        assert strategy.should_reconcile("lib1", False) is True

    def test_manual_strategy_never_reconciles(self):
        strategy = ManualStrategy()
        assert strategy.should_reconcile("lib1", True) is False
        assert strategy.should_reconcile("lib1", False) is False

    def test_hybrid_strategy_only_syncs_when_behind(self):
        strategy = HybridStrategy()
        assert strategy.should_reconcile("lib1", True) is False
        assert strategy.should_reconcile("lib1", False) is True


class TestWorkflowResult:
    """WorkflowResult 测试"""

    def test_success_result(self):
        result = WorkflowResult(
            success=True,
            message="工作流成功",
            new_state=RepoState.COMMITTED,
        )
        assert result.success is True
        assert result.new_state == RepoState.COMMITTED

    def test_failure_result(self):
        result = WorkflowResult(
            success=False,
            message="工作流失败",
            error=ErrorState.PERMISSION_ERROR,
        )
        assert result.success is False
        assert result.error == ErrorState.PERMISSION_ERROR


class TestWorkflowEngine:
    """WorkflowEngine 测试"""

    def test_init(self, workflow_engine, tmp_path):
        assert workflow_engine.repo_root == tmp_path
        assert workflow_engine.git_ops is not None
        assert isinstance(workflow_engine.strategy, AutoStrategy)

    def test_init_with_custom_strategy(self, tmp_path):
        engine = WorkflowEngine(tmp_path, strategy=ManualStrategy())
        assert isinstance(engine.strategy, ManualStrategy)

    def test_get_state(self, workflow_engine):
        assert workflow_engine.get_state() == RepoState.DIRTY

    def test_get_allowed_events(self, workflow_engine):
        events = workflow_engine.get_allowed_events()
        assert all(isinstance(e, Event) for e in events)


class TestWorkflowEngineDocCheck:
    """WorkflowEngine.doc_check() 测试"""

    def test_doc_check_consistent(self, workflow_engine_with_mock):
        workflow_engine_with_mock.git_ops.check_consistency.return_value = (
            ConsistencyResult(
                success=True,
                is_consistent=True,
                message="一致",
            )
        )

        result = workflow_engine_with_mock.doc_check(Path("submodules.yaml"))

        assert result.is_consistent is True

    def test_doc_check_inconsistent(self, workflow_engine_with_mock):
        workflow_engine_with_mock.git_ops.check_consistency.return_value = (
            ConsistencyResult(
                success=False,
                is_consistent=False,
                message="不一致",
            )
        )

        result = workflow_engine_with_mock.doc_check(Path("submodules.yaml"))

        assert result.is_consistent is False


class TestWorkflowEngineSyncSubmodules:
    """WorkflowEngine.sync_submodules() 测试"""

    def test_sync_requires_consistent_state(self, workflow_engine):
        workflow_engine.machine.state = RepoState.DIRTY

        result = workflow_engine.sync_submodules()

        assert result.success is False
        assert "不允许同步" in result.message

    def test_sync_success(self, workflow_engine_with_mock):
        workflow_engine_with_mock.machine.state = RepoState.CLEAN_AND_CONSISTENT
        workflow_engine_with_mock.git_ops.sync_submodules.return_value = SyncResult(
            success=True,
            message="同步完成",
        )

        result = workflow_engine_with_mock.sync_submodules()

        assert result.success is True

    def test_sync_failure(self, workflow_engine_with_mock):
        workflow_engine_with_mock.machine.state = RepoState.CLEAN_AND_CONSISTENT
        workflow_engine_with_mock.git_ops.sync_submodules.return_value = SyncResult(
            success=False,
            message="同步失败",
            error="git error",
        )

        result = workflow_engine_with_mock.sync_submodules()

        assert result.success is False


class TestWorkflowEngineCommitAndPush:
    """WorkflowEngine.commit_and_push() 测试"""

    def test_commit_requires_sync_state(self, workflow_engine):
        workflow_engine.machine.state = RepoState.CLEAN_AND_CONSISTENT

        result = workflow_engine.commit_and_push("test")

        assert result.success is False
        assert "不允许提交" in result.message

    def test_commit_success(self, workflow_engine_with_mock):
        workflow_engine_with_mock.machine.state = RepoState.COMMITTED
        workflow_engine_with_mock.git_ops.commit_and_push.return_value = PushResult(
            success=True,
            message="推送成功",
            commit_sha="abc1234",
        )

        result = workflow_engine_with_mock.commit_and_push("test commit")

        assert result.success is True
        assert result.commit_sha == "abc1234"

    def test_commit_failure(self, workflow_engine_with_mock):
        workflow_engine_with_mock.machine.state = RepoState.COMMITTED
        workflow_engine_with_mock.git_ops.commit_and_push.return_value = PushResult(
            success=False,
            message="推送失败",
            error="network error",
        )

        result = workflow_engine_with_mock.commit_and_push("test commit")

        assert result.success is False


class TestWorkflowEngineStandardWorkflow:
    """WorkflowEngine.run_standard_workflow() 测试"""

    def test_standard_workflow_consistency_fail(self, workflow_engine_with_mock):
        workflow_engine_with_mock.git_ops.check_consistency.return_value = (
            ConsistencyResult(
                success=False, is_consistent=False, message="不一致"
            )
        )

        result = workflow_engine_with_mock.run_standard_workflow(
            Path("submodules.yaml")
        )

        assert result.success is False
        assert "一致性检查失败" in result.message

    def test_standard_workflow_sync_fail(self, workflow_engine_with_mock):
        workflow_engine_with_mock.git_ops.check_consistency.return_value = (
            ConsistencyResult(
                success=True, is_consistent=True, message="一致"
            )
        )
        workflow_engine_with_mock.git_ops.sync_submodules.return_value = SyncResult(
            success=False, message="同步失败", error="git error"
        )

        result = workflow_engine_with_mock.run_standard_workflow(
            Path("submodules.yaml")
        )

        assert result.success is False
        assert "子模块同步失败" in result.message

    def test_standard_workflow_commit_fail(self, workflow_engine_with_mock):
        workflow_engine_with_mock.git_ops.check_consistency.return_value = (
            ConsistencyResult(
                success=True, is_consistent=True, message="一致"
            )
        )
        workflow_engine_with_mock.git_ops.sync_submodules.return_value = SyncResult(
            success=True, message="同步完成"
        )
        workflow_engine_with_mock.git_ops.commit_and_push.return_value = PushResult(
            success=False, message="推送失败", error="network"
        )

        result = workflow_engine_with_mock.run_standard_workflow(
            Path("submodules.yaml")
        )

        assert result.success is False
        assert "提交推送失败" in result.message


class TestWorkflowEngineAppendJournal:
    """WorkflowEngine.append_journal() 测试"""

    def test_append_journal_creates_file(self, workflow_engine, tmp_path):
        journal_dir = tmp_path / "meta" / "journal"
        journal_dir.mkdir(parents=True)

        results = [
            {"success": True, "repo": "lib1", "types": "sync"},
            {"success": False, "repo": "lib2", "types": "push"},
        ]

        workflow_engine.append_journal(results)

        today_files = list(journal_dir.glob("*.md"))
        assert len(today_files) == 1

    def test_append_journal_skips_empty_results(self, workflow_engine, tmp_path):
        workflow_engine.append_journal([])

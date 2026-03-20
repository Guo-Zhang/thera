"""
用户功能测试

测试 workflow status/history/audit 命令。
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from thera.fsm import ErrorState, Event, RepoState
from thera.workflow import (
    AutoStrategy,
    HybridStrategy,
    ManualStrategy,
    WorkflowEngine,
)


@pytest.fixture
def engine(tmp_path):
    """创建 WorkflowEngine 实例"""
    return WorkflowEngine(tmp_path)


class TestWorkflowStatus:
    """workflow status 测试"""

    def test_get_status_dirty(self, engine):
        """测试 DIRTY 状态"""
        status = engine.get_status()
        
        assert status["state"] == RepoState.DIRTY
        assert status["is_error"] is False
        assert Event.DOC_CHECK_OK in status["allowed_events"]
        assert Event.DOC_CHECK_FAIL in status["allowed_events"]

    def test_get_status_with_history(self, engine):
        """测试带历史的 status"""
        engine.machine.transition(Event.DOC_CHECK_OK)
        
        status = engine.get_status()
        assert status["history_count"] == 1

    def test_get_error_details_no_error(self, engine):
        """测试无错误时的详情"""
        details = engine.get_error_details()
        assert details is None

    def test_get_error_details_with_error(self, engine):
        """测试有错误时的详情"""
        engine.machine.state = ErrorState.NETWORK_ERROR
        engine.machine.error = ErrorState.NETWORK_ERROR
        
        details = engine.get_error_details()
        assert details is not None
        assert details["error"] == ErrorState.NETWORK_ERROR
        assert "检查网络" in details["suggestion"]


class TestWorkflowHistory:
    """workflow history 测试"""

    def test_get_history_empty(self, engine):
        """测试空历史"""
        history = engine.get_history()
        assert history == []

    def test_get_history_with_entries(self, engine):
        """测试有记录的历史"""
        engine.machine.transition(Event.DOC_CHECK_OK)
        engine.machine.transition(Event.SUBMODULE_SYNC)
        
        history = engine.get_history()
        assert len(history) == 2
        assert history[0]["from_state"] == RepoState.DIRTY
        assert history[0]["event"] == Event.DOC_CHECK_OK
        assert history[1]["from_state"] == RepoState.CLEAN_AND_CONSISTENT
        assert history[1]["event"] == Event.SUBMODULE_SYNC

    def test_get_history_limit(self, engine):
        """测试历史条数限制"""
        engine.machine.history = [
            (RepoState.DIRTY, Event.DOC_CHECK_OK),
            (RepoState.CLEAN_AND_CONSISTENT, Event.SUBMODULE_SYNC),
            (RepoState.SYNCED, Event.AUTO_COMMIT),
        ]
        
        history = engine.get_history(limit=2)
        assert len(history) == 2
        assert history[0]["from_state"] == RepoState.CLEAN_AND_CONSISTENT
        assert history[1]["from_state"] == RepoState.SYNCED


class TestWorkflowAudit:
    """workflow audit 测试"""

    def test_audit_empty(self, engine):
        """测试空审计"""
        report = engine.audit()
        
        assert report["total_transitions"] == 0
        assert report["error_count"] == 0
        assert report["state_distribution"] == {}

    def test_audit_with_transitions(self, engine):
        """测试有转移的审计"""
        engine.machine.transition(Event.DOC_CHECK_OK)
        engine.machine.transition(Event.SUBMODULE_SYNC)
        
        report = engine.audit()
        
        assert report["total_transitions"] == 2
        assert "DIRTY" in report["state_distribution"]
        assert "CLEAN_AND_CONSISTENT" in report["state_distribution"]


class TestConvergenceStrategy:
    """收敛策略测试"""

    def test_auto_strategy(self, engine):
        """测试自动策略"""
        engine.set_strategy("auto")
        assert isinstance(engine.strategy, AutoStrategy)
        assert engine.get_strategy_name() == "auto"

    def test_manual_strategy(self, engine):
        """测试手动策略"""
        engine.set_strategy("manual")
        assert isinstance(engine.strategy, ManualStrategy)
        assert engine.get_strategy_name() == "manual"

    def test_hybrid_strategy(self, engine):
        """测试混合策略"""
        engine.set_strategy("hybrid")
        assert isinstance(engine.strategy, HybridStrategy)
        assert engine.get_strategy_name() == "hybrid"

    def test_invalid_strategy(self, engine):
        """测试无效策略"""
        with pytest.raises(ValueError):
            engine.set_strategy("invalid")

    def test_strategy_should_reconcile(self, engine):
        """测试策略行为"""
        engine.set_strategy("auto")
        assert engine.strategy.should_reconcile("lib", True) is True
        assert engine.strategy.should_reconcile("lib", False) is True
        
        engine.set_strategy("manual")
        assert engine.strategy.should_reconcile("lib", True) is False
        assert engine.strategy.should_reconcile("lib", False) is False
        
        engine.set_strategy("hybrid")
        assert engine.strategy.should_reconcile("lib", True) is False
        assert engine.strategy.should_reconcile("lib", False) is True

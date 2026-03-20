"""测试 FSM 模块"""

import pytest

from thera.fsm import (
    ALLOWED_EVENTS,
    TRANSITIONS,
    ErrorState,
    Event,
    IllegalTransitionError,
    RepoState,
    StateMachine,
    SubmoduleState,
)


class TestRepoState:
    """测试 RepoState 枚举"""

    def test_all_states_defined(self):
        """验证所有状态都定义"""
        assert RepoState.DIRTY is not None
        assert RepoState.CLEAN_AND_CONSISTENT is not None
        assert RepoState.INCONSISTENT is not None
        assert RepoState.SYNCED is not None
        assert RepoState.COMMITTED is not None

    def test_state_count(self):
        """验证状态数量"""
        assert len(RepoState) == 5


class TestSubmoduleState:
    """测试 SubmoduleState 枚举"""

    def test_all_states_defined(self):
        """验证所有状态都定义"""
        assert SubmoduleState.BEHIND is not None
        assert SubmoduleState.UP_TO_DATE is not None
        assert SubmoduleState.DETACHED is not None


class TestErrorState:
    """测试 ErrorState 枚举"""

    def test_all_states_defined(self):
        """验证所有状态都定义"""
        assert ErrorState.NETWORK_ERROR is not None
        assert ErrorState.CONSISTENCY_ERROR is not None
        assert ErrorState.DETACHED_HEAD_ERROR is not None
        assert ErrorState.PERMISSION_ERROR is not None


class TestEvent:
    """测试 Event 枚举"""

    def test_all_events_defined(self):
        """验证所有事件都定义"""
        assert Event.EDIT is not None
        assert Event.DOC_CHECK_OK is not None
        assert Event.DOC_CHECK_FAIL is not None
        assert Event.FIX is not None
        assert Event.SUBMODULE_SYNC is not None
        assert Event.AUTO_COMMIT is not None
        assert Event.PUSH_OK is not None
        assert Event.PUSH_FAIL is not None


class TestStateMachine:
    """测试 StateMachine 类"""

    def test_initial_state_is_dirty(self):
        """初始状态应为 DIRTY"""
        machine = StateMachine()
        assert machine.state == RepoState.DIRTY

    def test_initial_no_error(self):
        """初始无错误状态"""
        machine = StateMachine()
        assert machine.error is None

    def test_initial_history_empty(self):
        """初始历史为空"""
        machine = StateMachine()
        assert machine.history == []

    def test_valid_transition_m0_to_m1(self):
        """M0 + DOC_CHECK_OK → M1"""
        machine = StateMachine()
        machine.transition(Event.DOC_CHECK_OK)
        assert machine.state == RepoState.CLEAN_AND_CONSISTENT

    def test_valid_transition_m0_to_m2(self):
        """M0 + DOC_CHECK_FAIL → M2"""
        machine = StateMachine()
        machine.transition(Event.DOC_CHECK_FAIL)
        assert machine.state == RepoState.INCONSISTENT

    def test_valid_transition_m1_to_m0(self):
        """M1 + EDIT → M0"""
        machine = StateMachine()
        machine.transition(Event.DOC_CHECK_OK)
        machine.transition(Event.EDIT)
        assert machine.state == RepoState.DIRTY

    def test_valid_transition_m1_to_m3(self):
        """M1 + SUBMODULE_SYNC → M3"""
        machine = StateMachine()
        machine.transition(Event.DOC_CHECK_OK)
        machine.transition(Event.SUBMODULE_SYNC)
        assert machine.state == RepoState.SYNCED

    def test_valid_transition_m2_to_m1(self):
        """M2 + FIX → M1"""
        machine = StateMachine()
        machine.transition(Event.DOC_CHECK_FAIL)
        machine.transition(Event.FIX)
        assert machine.state == RepoState.CLEAN_AND_CONSISTENT

    def test_valid_transition_m3_to_m4(self):
        """M3 + AUTO_COMMIT → M4"""
        machine = StateMachine()
        machine.transition(Event.DOC_CHECK_OK)
        machine.transition(Event.SUBMODULE_SYNC)
        machine.transition(Event.AUTO_COMMIT)
        assert machine.state == RepoState.COMMITTED

    def test_valid_transition_m4_to_m1(self):
        """M4 + PUSH_OK → M1"""
        machine = StateMachine()
        machine.transition(Event.DOC_CHECK_OK)
        machine.transition(Event.SUBMODULE_SYNC)
        machine.transition(Event.AUTO_COMMIT)
        machine.transition(Event.PUSH_OK)
        assert machine.state == RepoState.CLEAN_AND_CONSISTENT

    def test_valid_transition_m4_to_error(self):
        """M4 + PUSH_FAIL → Error"""
        machine = StateMachine()
        machine.transition(Event.DOC_CHECK_OK)
        machine.transition(Event.SUBMODULE_SYNC)
        machine.transition(Event.AUTO_COMMIT)
        machine.transition(Event.PUSH_FAIL)
        assert machine.state == ErrorState.NETWORK_ERROR
        assert machine.error == ErrorState.NETWORK_ERROR

    def test_illegal_transition_raises(self):
        """M0 + SUBMODULE_SYNC 应抛出异常"""
        machine = StateMachine()
        with pytest.raises(IllegalTransitionError):
            machine.transition(Event.SUBMODULE_SYNC)

    def test_illegal_transition_m0_auto_commit(self):
        """M0 + AUTO_COMMIT 应抛出异常"""
        machine = StateMachine()
        with pytest.raises(IllegalTransitionError):
            machine.transition(Event.AUTO_COMMIT)

    def test_illegal_transition_m2_submodule_sync(self):
        """M2 + SUBMODULE_SYNC 应抛出异常"""
        machine = StateMachine()
        machine.transition(Event.DOC_CHECK_FAIL)
        with pytest.raises(IllegalTransitionError):
            machine.transition(Event.SUBMODULE_SYNC)

    def test_history_records_transitions(self):
        """历史记录转移"""
        machine = StateMachine()
        machine.transition(Event.DOC_CHECK_OK)
        machine.transition(Event.EDIT)
        assert len(machine.history) == 2
        assert machine.history[0] == (RepoState.DIRTY, Event.DOC_CHECK_OK)
        assert machine.history[1] == (RepoState.CLEAN_AND_CONSISTENT, Event.EDIT)

    def test_can_transition_returns_true_for_valid(self):
        """can_transition 对有效转移返回 True"""
        machine = StateMachine()
        assert machine.can_transition(Event.DOC_CHECK_OK) is True
        assert machine.can_transition(Event.DOC_CHECK_FAIL) is True

    def test_can_transition_returns_false_for_invalid(self):
        """can_transition 对无效转移返回 False"""
        machine = StateMachine()
        assert machine.can_transition(Event.SUBMODULE_SYNC) is False
        assert machine.can_transition(Event.AUTO_COMMIT) is False

    def test_get_allowed_events(self):
        """获取允许的事件"""
        machine = StateMachine()
        events = machine.get_allowed_events()
        assert Event.DOC_CHECK_OK in events
        assert Event.DOC_CHECK_FAIL in events
        assert Event.SUBMODULE_SYNC not in events

    def test_is_error_state_false_initially(self):
        """初始不是错误状态"""
        machine = StateMachine()
        assert machine.is_error_state() is False

    def test_is_error_state_true_after_push_fail(self):
        """推送失败后是错误状态"""
        machine = StateMachine()
        machine.transition(Event.DOC_CHECK_OK)
        machine.transition(Event.SUBMODULE_SYNC)
        machine.transition(Event.AUTO_COMMIT)
        machine.transition(Event.PUSH_FAIL)
        assert machine.is_error_state() is True


class TestTransitionsTable:
    """测试转移表"""

    def test_all_states_have_transitions(self):
        """所有状态都有转移定义"""
        for state in RepoState:
            assert state in TRANSITIONS

    def test_all_states_have_allowed_events(self):
        """所有状态都有允许事件定义"""
        for state in RepoState:
            assert state in ALLOWED_EVENTS

    def test_terminal_state_has_push_transitions(self):
        """终态有 push 相关转移"""
        assert Event.PUSH_OK in ALLOWED_EVENTS[RepoState.COMMITTED]
        assert Event.PUSH_FAIL in ALLOWED_EVENTS[RepoState.COMMITTED]


class TestStateMachineHooks:
    """测试状态机钩子"""

    def test_add_enter_hook(self):
        """测试添加进入状态钩子"""
        machine = StateMachine()
        called = []
        
        def callback(old, event):
            called.append((old, event))
        
        machine.add_enter_hook(RepoState.CLEAN_AND_CONSISTENT, callback)
        machine.transition(Event.DOC_CHECK_OK)
        
        assert len(called) == 1
        assert called[0] == (RepoState.DIRTY, Event.DOC_CHECK_OK)

    def test_add_exit_hook(self):
        """测试添加退出状态钩子"""
        machine = StateMachine()
        called = []
        
        def callback(old, event):
            called.append((old, event))
        
        machine.add_exit_hook(RepoState.DIRTY, callback)
        machine.transition(Event.DOC_CHECK_OK)
        
        assert len(called) == 1
        assert called[0] == (RepoState.DIRTY, Event.DOC_CHECK_OK)

    def test_multiple_hooks(self):
        """测试多个钩子"""
        machine = StateMachine()
        calls = []
        
        def callback1(old, event):
            calls.append("callback1")
        
        def callback2(old, event):
            calls.append("callback2")
        
        machine.add_enter_hook(RepoState.CLEAN_AND_CONSISTENT, callback1)
        machine.add_enter_hook(RepoState.CLEAN_AND_CONSISTENT, callback2)
        machine.transition(Event.DOC_CHECK_OK)
        
        assert len(calls) == 2
        assert "callback1" in calls
        assert "callback2" in calls

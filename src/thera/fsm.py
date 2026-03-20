"""
状态机核心模块

定义状态、事件、转移规则，验证状态转移的合法性。
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class RepoState(Enum):
    """主仓库状态"""
    DIRTY = auto()  # M0: 有变更未提交
    CLEAN_AND_CONSISTENT = auto()  # M1: 干净且一致
    INCONSISTENT = auto()  # M2: 配置不一致
    SYNCED = auto()  # M3: 子模块已同步
    COMMITTED = auto()  # M4: 变更已提交


class SubmoduleState(Enum):
    """子模块状态"""
    BEHIND = auto()  # S0: 落后远程
    UP_TO_DATE = auto()  # S1: 已同步
    DETACHED = auto()  # S2: 分离头指针


class ErrorState(Enum):
    """错误状态"""
    NETWORK_ERROR = auto()  # E1: 网络问题
    CONSISTENCY_ERROR = auto()  # E2: 一致性失败
    DETACHED_HEAD_ERROR = auto()  # E3: 分离头指针
    PERMISSION_ERROR = auto()  # E4: 权限不足


class Event(Enum):
    """状态转移事件"""
    EDIT = auto()  # 修改文件
    DOC_CHECK_OK = auto()  # 一致性检查通过
    DOC_CHECK_FAIL = auto()  # 一致性检查失败
    FIX = auto()  # 手动修复
    SUBMODULE_SYNC = auto()  # 子模块同步
    AUTO_COMMIT = auto()  # 自动提交
    PUSH_OK = auto()  # 推送成功
    PUSH_FAIL = auto()  # 推送失败


# 状态转移表
TRANSITIONS: dict[RepoState, dict[Event, RepoState | ErrorState]] = {
    RepoState.DIRTY: {
        Event.DOC_CHECK_OK: RepoState.CLEAN_AND_CONSISTENT,
        Event.DOC_CHECK_FAIL: RepoState.INCONSISTENT,
    },
    RepoState.CLEAN_AND_CONSISTENT: {
        Event.EDIT: RepoState.DIRTY,
        Event.SUBMODULE_SYNC: RepoState.SYNCED,
    },
    RepoState.INCONSISTENT: {
        Event.FIX: RepoState.CLEAN_AND_CONSISTENT,
    },
    RepoState.SYNCED: {
        Event.AUTO_COMMIT: RepoState.COMMITTED,
    },
    RepoState.COMMITTED: {
        Event.PUSH_OK: RepoState.CLEAN_AND_CONSISTENT,
        Event.PUSH_FAIL: ErrorState.NETWORK_ERROR,
    },
}

# 允许的事件（用于提示用户）
ALLOWED_EVENTS: dict[RepoState, list[Event]] = {
    RepoState.DIRTY: [Event.DOC_CHECK_OK, Event.DOC_CHECK_FAIL],
    RepoState.CLEAN_AND_CONSISTENT: [Event.EDIT, Event.SUBMODULE_SYNC],
    RepoState.INCONSISTENT: [Event.FIX],
    RepoState.SYNCED: [Event.AUTO_COMMIT],
    RepoState.COMMITTED: [Event.PUSH_OK, Event.PUSH_FAIL],
}


class StateMachineError(Exception):
    """状态机异常基类"""
    pass


class IllegalTransitionError(StateMachineError):
    """非法转移异常"""

    def __init__(self, current: RepoState, event: Event):
        self.current = current
        self.event = event
        super().__init__(f"非法转移: {current.name} + {event.name}")


@dataclass
class StateMachine:
    """Git 状态机"""
    state: RepoState | ErrorState = RepoState.DIRTY
    error: Optional[ErrorState] = None
    history: list[tuple[RepoState, Event]] = field(default_factory=list)
    on_enter_callbacks: dict = field(default_factory=dict)
    on_exit_callbacks: dict = field(default_factory=dict)

    def add_enter_hook(self, state: RepoState | ErrorState, callback) -> None:
        """添加进入状态时的钩子"""
        if state not in self.on_enter_callbacks:
            self.on_enter_callbacks[state] = []
        self.on_enter_callbacks[state].append(callback)

    def add_exit_hook(self, state: RepoState, callback) -> None:
        """添加退出状态时的钩子"""
        if state not in self.on_exit_callbacks:
            self.on_exit_callbacks[state] = []
        self.on_exit_callbacks[state].append(callback)

    def can_transition(self, event: Event) -> bool:
        """检查是否可以转移"""
        return event in ALLOWED_EVENTS.get(self.state, [])  # type: ignore

    def transition(self, event: Event) -> RepoState | ErrorState:
        """执行状态转移"""
        if not self.can_transition(event):
            raise IllegalTransitionError(self.state, event)  # type: ignore

        old_state = self.state
        new_state = TRANSITIONS[self.state][event]  # type: ignore

        for callback in self.on_exit_callbacks.get(old_state, []):
            callback(old_state, event)

        self.history.append((old_state, event))  # type: ignore
        self.state = new_state

        if event == Event.PUSH_FAIL:
            self.error = ErrorState.NETWORK_ERROR

        for callback in self.on_enter_callbacks.get(new_state, []):
            callback(old_state, event)

        return new_state

    def get_allowed_events(self) -> list[Event]:
        """获取当前状态允许的事件"""
        return ALLOWED_EVENTS.get(self.state, [])  # type: ignore

    def is_error_state(self) -> bool:
        """是否处于错误状态"""
        return self.error is not None

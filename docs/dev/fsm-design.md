# 状态机设计

## 1. 设计目标

1. **显式追踪**：每个仓库实例都有明确的状态标识
2. **转移验证**：非法转移必须被拒绝，而非静默忽略
3. **错误可追踪**：错误状态需要分类，便于问题诊断

## 2. 状态定义

### 2.1 主仓库状态

```python
from enum import Enum, auto

class RepoState(Enum):
    """主仓库状态"""
    DIRTY = auto()              # M0: 有变更未提交
    CLEAN_AND_CONSISTENT = auto()  # M1: 干净且一致
    INCONSISTENT = auto()       # M2: 配置不一致
    SYNCED = auto()             # M3: 子模块已同步
    COMMITTED = auto()          # M4: 变更已提交
```

### 2.2 子模块状态

```python
class SubmoduleState(Enum):
    """子模块状态"""
    BEHIND = auto()            # S0: 落后远程
    UP_TO_DATE = auto()         # S1: 已同步
    DETACHED = auto()          # S2: 分离头指针
```

### 2.3 错误状态

```python
class ErrorState(Enum):
    """错误状态"""
    NETWORK_ERROR = auto()      # E1: 网络问题
    CONSISTENCY_ERROR = auto()  # E2: 一致性失败
    DETACHED_HEAD_ERROR = auto()  # E3: 分离头指针
    PERMISSION_ERROR = auto()  # E4: 权限不足
```

## 3. 事件定义

```python
class Event(Enum):
    """状态转移事件"""
    EDIT = auto()               # 修改文件
    DOC_CHECK_OK = auto()       # 一致性检查通过
    DOC_CHECK_FAIL = auto()     # 一致性检查失败
    FIX = auto()                # 手动修复
    SUBMODULE_SYNC = auto()     # 子模块同步
    AUTO_COMMIT = auto()        # 自动提交
    PUSH_OK = auto()            # 推送成功
    PUSH_FAIL = auto()          # 推送失败
```

## 4. 转移规则矩阵

```python
# 状态转移表
TRANSITIONS: dict[RepoState, dict[Event, RepoState]] = {
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
        Event.PUSH_FAIL: ErrorState.NETWORK_ERROR,  # 特殊：转到错误态
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
```

## 5. StateMachine 类实现

```python
from dataclasses import dataclass, field
from typing import Optional

class StateMachineError(Exception):
    """状态机异常"""
    pass

class IllegalTransitionError(StateMachineError):
    """非法转移异常"""
    def __init__(self, current: RepoState, event: Event):
        self.current = current
        self.event = event
        super().__init__(
            f"非法转移: {current.name} + {event.name}"
        )

@dataclass
class StateMachine:
    """Git 状态机"""
    state: RepoState = RepoState.DIRTY
    error: Optional[ErrorState] = None
    history: list[tuple[RepoState, Event]] = field(default_factory=list)
    
    def can_transition(self, event: Event) -> bool:
        """检查是否可以转移"""
        if event == Event.PUSH_FAIL:
            return self.state == RepoState.COMMITTED
        return event in ALLOWED_EVENTS.get(self.state, [])
    
    def transition(self, event: Event) -> RepoState:
        """执行状态转移"""
        if not self.can_transition(event):
            raise IllegalTransitionError(self.state, event)
        
        old_state = self.state
        new_state = TRANSITIONS[self.state][event]
        
        self.history.append((old_state, event))
        self.state = new_state
        
        # 如果是推送失败，记录错误状态
        if event == Event.PUSH_FAIL:
            self.error = ErrorState.NETWORK_ERROR
        
        return new_state
    
    def get_allowed_events(self) -> list[Event]:
        """获取当前状态允许的事件"""
        return ALLOWED_EVENTS.get(self.state, [])
    
    def is_error_state(self) -> bool:
        """是否处于错误状态"""
        return self.error is not None
```

## 6. 使用示例

```python
from thera.fsm import StateMachine, RepoState, Event

# 创建状态机（默认从 DIRTY 开始）
machine = StateMachine(RepoState.DIRTY)

# 执行工作流
try:
    # 1. 检查一致性
    is_consistent = git_ops.check_consistency(yaml_path)
    if is_consistent:
        machine.transition(Event.DOC_CHECK_OK)
    else:
        machine.transition(Event.DOC_CHECK_FAIL)
    
    # 2. 检查当前状态是否允许同步
    if Event.SUBMODULE_SYNC in machine.get_allowed_events():
        git_ops.sync_submodules()
        machine.transition(Event.SUBMODULE_SYNC)
    
    # 3. 自动提交
    if Event.AUTO_COMMIT in machine.get_allowed_events():
        result = git_ops.commit_and_push(message)
        if result.success:
            machine.transition(Event.PUSH_OK)
        else:
            machine.transition(Event.PUSH_FAIL)
            # 处理错误
            handle_error(machine.error)
            
except IllegalTransitionError as e:
    print(f"错误: {e}")
    print(f"当前状态: {machine.state.name}")
    print(f"允许的事件: {[e.name for e in machine.get_allowed_events()]}")
```

## 7. 错误处理策略

| 错误类型 | 检测时机 | 处理策略 |
|----------|----------|----------|
| NETWORK_ERROR | push 时网络超时 | 等待重试或人工介入 |
| CONSISTENCY_ERROR | doc-check 失败 | 提示用户修复 YAML/.gitmodules |
| DETACHED_HEAD_ERROR | submodule-sync 检测到 | 提示用户在子模块执行 checkout |
| PERMISSION_ERROR | git 操作权限不足 | 提示检查文件权限 |

## 8. 日志记录

每次状态转移应记录：

```python
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def log_transition(machine: StateMachine, event: Event, details: dict = None):
    """记录状态转移"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "from_state": machine.history[-1][0].name if machine.history else None,
        "event": event.name,
        "to_state": machine.state.name,
        "details": details or {},
    }
    logger.info(f"状态转移: {entry}")
```

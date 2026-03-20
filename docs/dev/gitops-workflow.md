# GitOps 工作流设计

## 1. 设计目标

GitOps 层是**创造性**的层次，回答"我们能创造出什么新模式"。

| 目标 | 说明 |
|------|------|
| **声明式期望** | YAML 定义期望状态，而非命令式步骤 |
| **自动收敛** | 检测漂移后自动或半自动修复 |
| **可组合** | 工作流可以像函数一样组合 |
| **可观测** | 状态变更历史可追溯 |

## 2. 范畴论基础

### 2.1 基本概念

| 范畴论概念 | GitOps 对应 |
|------------|-------------|
| 对象 (Object) | 仓库状态、子模块状态 |
| 态射 (Morphism) | 状态转移操作 |
| 函子 (Functor) | 子模块状态 → 主仓库状态的映射 |
| 自然变换 | 工作流之间的转换 |
| 单子 (Monad) | 副作用处理（错误、网络） |

### 2.2 工作流函子

```python
# 工作流是态射：RepoState → RepoState
@dataclass
class Workflow(Generic[S, T]):
    """工作流函子"""
    name: str
    run: Callable[[S], Result[T, Error]]
    
    def compose(self, other: Workflow) -> Workflow:
        """工作流组合"""
        def composed(state):
            result = other.run(state)
            if isinstance(result, Ok):
                return self.run(result.value)
            return result
        return Workflow(
            name=f"{self.name} ∘ {other.name}",
            run=composed
        )
```

## 3. 基础工作流

### 3.1 基本工作流函子

```python
# 检查一致性
CheckConsistency = Workflow(
    name="CheckConsistency",
    run=lambda state: Ok(state) if doc_check() else Err(ConsistencyError)
)

# 同步子模块
SyncSubmodules = Workflow(
    name="SyncSubmodules",
    run=lambda state: Ok(state) if sync() else Err(SyncError)
)

# 提交推送
CommitAndPush = Workflow(
    name="CommitAndPush",
    run=lambda state: Ok(state) if commit() else Err(CommitError)
)
```

### 3.2 工作流组合

```python
# 标准工作流：CheckConsistency → SyncSubmodules → CommitAndPush
StandardWorkflow = CheckConsistency.compose(SyncSubmodules).compose(CommitAndPush)

# 等价于：
StandardWorkflow = CheckConsistency ∘ SyncSubmodules ∘ CommitAndPush
```

### 3.3 组合定律验证

工作流组合满足范畴论定律：

```python
# 结合律
(W1 ∘ W2) ∘ W3 == W1 ∘ (W2 ∘ W3)

# 恒等态射
Workflow.id ∘ W == W == W ∘ Workflow.id
```

## 4. 期望状态设计

### 4.1 YAML Schema

```yaml
# expected_state.yaml
version: "1"
spec:
  submodules:
    - name: "archive"
      path: "docs/archive"
      url: "https://github.com/quanttide/..."
      expected_ref: "main"  # 期望的分支/标签
    - name: "thera"
      path: "src/thera"
      url: "https://github.com/Guo-Zhang/thera.git"
      expected_ref: "v0.3.0"
  
  consistency:
    yaml_source: "meta/profile/submodules.yaml"
    gitmodules: ".gitmodules"
  
  sync_policy:
    mode: "auto"  # auto | manual | hybrid
    auto_on:
      - "commit"
      - "push"
```

### 4.2 状态差异

```python
@dataclass
class Drift:
    """配置漂移"""
    submodule: str
    current: str  # 当前 commit
    expected: str  # 期望 commit
    severity: Literal["info", "warning", "critical"]
```

## 5. 收敛策略

### 5.1 策略类型

| 策略 | 行为 | 适用场景 |
|------|------|----------|
| `auto` | 自动修复，无需人工 | 测试环境、低风险变更 |
| `manual` | 检测到漂移后等待人工确认 | 生产环境、高风险变更 |
| `hybrid` | 自动修复低风险，人工确认高风险 | 混合环境 |

### 5.2 策略选择器

```python
class ConvergenceStrategy(ABC):
    """收敛策略基类"""
    
    @abstractmethod
    def should_reconcile(self, drift: Drift) -> bool:
        """判断是否应该自动收敛"""
        pass

class AutoStrategy(ConvergenceStrategy):
    def should_reconcile(self, drift: Drift) -> bool:
        return True

class ManualStrategy(ConvergenceStrategy):
    def should_reconcile(self, drift: Drift) -> bool:
        return False

class HybridStrategy(ConvergenceStrategy):
    def should_reconcile(self, drift: Drift) -> bool:
        return drift.severity in ["info", "warning"]
```

## 6. 副作用抽象（Error Monad）

### 6.1 Result 类型

```python
from dataclasses import dataclass
from typing import TypeVar, Generic

T = TypeVar('T')
E = TypeVar('E')

@dataclass
class Ok(Generic[T]):
    value: T

@dataclass
class Err(Generic[E]):
    error: E

Result = Ok[T] | Err[E]
```

### 6.2 Monad 实例

```python
def bind(result: Result[T, E], f: Callable[[T], Result[U, E]]) -> Result[U, E]:
    """Monad bind 操作"""
    if isinstance(result, Ok):
        return f(result.value)
    return result  # 传播错误

def map(result: Result[T, E], f: Callable[[T], U]) -> Result[U, E]:
    """Monad map 操作"""
    if isinstance(result, Ok):
        return Ok(f(result.value))
    return result
```

### 6.3 工作流中的错误处理

```python
# 使用 Monad 链式处理错误
workflow_result = (
    CheckConsistency.run(state)
    | bind(SyncSubmodules.run)
    | bind(CommitAndPush.run)
    | map(lambda s: log_to_journal(s))
)
```

## 7. 子模块 ↔ 主仓库 函子

### 7.1 函子定义

```python
class SubmoduleToMain(Functor):
    """子模块状态到主仓库状态的函子"""
    
    def map(self, submodule_state: S0 | S1 | S2) -> M0 | M1 | M2:
        """F(子模块状态) → 主仓库状态"""
        match submodule_state:
            case S0():  # Behind
                return M2  # Inconsistent
            case S1():  # UpToDate
                return M1  # CleanAndConsistent
            case S2():  # Detached
                return M2  # Inconsistent
```

### 7.2 自然变换

```python
def aggregate_submodule_states(states: list[S0 | S1 | S2]) -> M0 | M1 | M2:
    """聚合多个子模块状态为主仓库状态"""
    if any(isinstance(s, S2) for s in states):
        return M2
    if any(isinstance(s, S0) for s in states):
        return M2
    return M1
```

## 8. 工作流模式库

### 8.1 预定义工作流

```python
class WorkflowLibrary:
    """工作流模式库"""
    
    @staticmethod
    def standard() -> Workflow:
        """标准工作流"""
        return CheckConsistency ∘ SyncSubmodules ∘ CommitAndPush
    
    @staticmethod
    def readonly() -> Workflow:
        """只读检查"""
        return CheckConsistency
    
    @staticmethod
    def sync_only() -> Workflow:
        """仅同步"""
        return SyncSubmodules
    
    @staticmethod
    def emergency() -> Workflow:
        """紧急模式：跳过检查，直接同步"""
        return SyncSubmodules ∘ CommitAndPush
```

### 8.2 自定义工作流

```python
# 用户可以定义自己的组合
MyWorkflow = (
    CheckConsistency
    | optional(NotifySlack)  # 可选的通知步骤
    | SyncSubmodules
    | CommitAndPush
    | optional(LogToJournal)
)
```

## 9. 实现示例

```python
class WorkflowEngine:
    """GitOps 工作流引擎"""
    
    def __init__(self, repo_root: Path, strategy: ConvergenceStrategy):
        self.git_ops = GitOps(repo_root)
        self.fsm = StateMachine(RepoState.DIRTY)
        self.strategy = strategy
    
    def detect_drift(self) -> list[Drift]:
        """检测配置漂移"""
        expected = self._load_expected_state()
        actual = self.git_ops.get_submodule_status()
        
        drifts = []
        for submodule, info in actual.items():
            if submodule not in expected:
                continue
            exp = expected[submodule]
            if info.commit != exp.expected_ref:
                drifts.append(Drift(
                    submodule=submodule,
                    current=info.commit,
                    expected=exp.expected_ref,
                    severity=self._classify_drift(info, exp)
                ))
        return drifts
    
    def reconcile(self, drifts: list[Drift]) -> ReconcileResult:
        """收敛到期望状态"""
        results = []
        for drift in drifts:
            if self.strategy.should_reconcile(drift):
                result = self._apply_fix(drift)
                results.append(result)
            else:
                results.append(DriftReport(
                    drift=drift,
                    action="awaiting_manual_approval"
                ))
        return ReconcileResult(results)
    
    def run_workflow(self, workflow: Workflow) -> WorkflowResult:
        """执行工作流"""
        state = self.fsm.state
        result = workflow.run(state)
        
        if isinstance(result, Ok):
            self.fsm.transition(result.value)
        else:
            self._handle_error(result.error)
        
        return result
```

## 10. 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 工作流表示 | 函数组合 | 符合范畴论直觉 |
| 错误处理 | Result Monad | 显式处理，无异常泄漏 |
| 策略模式 | 依赖注入 | 支持不同收敛策略 |
| 状态聚合 | 自然变换 | 子模块 ↔ 主仓库映射 |

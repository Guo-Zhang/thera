# 迁移步骤

## 概述

从当前架构迁移到目标架构的详细步骤。

## 迁移原则

1. **小步重构**：每次只做一个小改动
2. **持续验证**：每个改动后立即测试
3. **向后兼容**：保留原有接口，确保 CLI 继续工作

## 阶段一：抽取 GitOps（无功能变更）

### 1.1 创建 git_ops.py

```python
# src/thera/src/thera/git_ops.py
import subprocess
from pathlib import Path
from dataclasses import dataclass
from enum import Enum, auto

# ... 完整实现见 git-ops-design.md
```

### 1.2 修改现有模块

每个模块改为导入 GitOps：

```python
# submodule_sync.py
from thera.git_ops import GitOps

def run_git(args, repo_root, capture=True):
    # 删除此函数，改用 GitOps
    ...

def get_submodule_status(repo_root):
    ops = GitOps(repo_root)
    return ops.get_submodule_status()
```

### 1.3 验证

```bash
# 确保原有功能不变
python3 src/thera/src/thera/cli.py doc-check
python3 src/thera/src/thera/cli.py submodule-sync --check
python3 src/thera/src/thera/cli.py auto-commit --dry-run
```

## 阶段二：引入状态机（并行运行）

### 2.1 创建 fsm.py

```python
# src/thera/src/thera/fsm.py
from enum import Enum, auto
from dataclasses import dataclass

# ... 完整实现见 fsm-design.md
```

### 2.2 创建 workflow_engine.py

```python
# src/thera/src/thera/workflow_engine.py
from pathlib import Path
from thera.git_ops import GitOps
from thera.fsm import StateMachine, RepoState, Event, IllegalTransitionError

class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self, repo_root: Path):
        self.git_ops = GitOps(repo_root)
        self.machine = StateMachine(RepoState.DIRTY)
    
    # ... 见 git-ops-design.md
```

### 2.3 测试新命令

```bash
# 新命令使用状态机
python3 src/thera/src/thera/workflow_cli.py --help
```

### 2.4 对比验证

```bash
# 在同一仓库上对比新旧命令结果
python3 src/thera/src/thera/cli.py doc-check
python3 src/thera/src/thera/workflow_cli.py doc-check

# 结果应该一致
```

## 阶段三：切换主入口

### 3.1 更新 cli.py

```python
# cli.py
def main():
    # ...
    if args.command == "auto-commit":
        # 使用新状态机
        engine = WorkflowEngine(repo_root)
        return engine.run_auto_commit(args)
    # ...
```

### 3.2 废弃旧函数

```python
# 标记为废弃
def run_git(args, repo_root, capture=True):
    import warnings
    warnings.warn(
        "run_git is deprecated, use GitOps instead",
        DeprecationWarning
    )
    ops = GitOps(repo_root)
    return ops.run_git(args, capture)
```

### 3.3 完整测试

```bash
# 完整工作流测试
python3 src/thera/src/thera/cli.py doc-check
python3 src/thera/src/thera/cli.py submodule-sync --check
python3 src/thera/src/thera/cli.py auto-commit --dry-run
python3 src/thera/src/thera/cli.py auto-commit
```

## 阶段四：清理与增强

### 4.1 删除废弃代码

```bash
# 确认所有调用已迁移后
git rm src/thera/src/thera/auto_commit.py
git rm src/thera/src/thera/doc_check.py
git rm src/thera/src/thera/submodule_sync.py
```

### 4.2 添加钩子

```python
# fsm.py
@dataclass
class StateMachine:
    # ...
    on_enter_callbacks: dict[RepoState, list] = field(default_factory=dict)
    on_exit_callbacks: dict[RepoState, list] = field(default_factory=dict)
    
    def add_enter_hook(self, state: RepoState, callback):
        """添加进入状态时的钩子"""
        if state not in self.on_enter_callbacks:
            self.on_enter_callbacks[state] = []
        self.on_enter_callbacks[state].append(callback)
    
    def add_exit_hook(self, state: RepoState, callback):
        """添加退出状态时的钩子"""
        if state not in self.on_exit_callbacks:
            self.on_exit_callbacks[state] = []
        self.on_exit_callbacks[state].append(callback)
```

### 4.3 添加日志

```python
# 在状态转移时记录日志
import logging

logger = logging.getLogger(__name__)

def transition(self, event: Event) -> RepoState:
    old_state = self.state
    new_state = TRANSITIONS[self.state][event]
    
    logger.info(
        f"状态转移: {old_state.name} + {event.name} -> {new_state.name}"
    )
    # ...
```

## 验证清单

每个阶段完成后，验证以下内容：

| 阶段 | 验证项 |
|------|--------|
| 一 | `cli.py` 功能不变 |
| 二 | 新旧命令结果一致 |
| 三 | 所有测试通过 |
| 四 | 代码无废弃警告 |

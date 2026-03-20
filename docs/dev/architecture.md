# 架构设计

## 1. 当前架构

```
src/thera/src/thera/
├── cli.py              # 统一入口，解析命令
├── auto_commit.py      # 自动提交推送（独立封装 run_git）
├── doc_check.py        # 一致性检查（独立封装 run_git）
└── submodule_sync.py   # 子模块同步（独立封装 run_git）
```

### 问题

| 问题 | 说明 |
|------|------|
| 代码重复 | 每个模块独立封装 `run_git()` 函数 |
| 状态不透明 | 各模块独立运行，不知道当前仓库状态 |
| 无顺序约束 | 可以跳过 doc-check 直接运行 auto-commit |
| 错误处理分散 | 失败时只返回退出码，无统一错误分类 |

## 2. 目标架构

```
src/thera/src/thera/
├── cli.py              # 入口层：解析命令，流程编排
├── fsm.py              # 状态机核心：状态定义、转移验证
├── git_ops.py          # Git 操作层：封装所有 git 操作
├── auto_commit.py      # 迁移到 git_ops
├── doc_check.py        # 迁移到 git_ops
└── submodule_sync.py   # 迁移到 git_ops
```

### 模块职责

| 模块 | 职责 | 对外接口 |
|------|------|----------|
| `cli.py` | 解析命令，调用状态机，格式化输出 | 命令行参数 |
| `fsm.py` | 定义状态、转移规则、验证合法性 | `StateMachine` 类 |
| `git_ops.py` | 封装 git 操作，返回明确结果 | `GitOps` 类 |

## 3. 数据流

```
┌─────────────┐
│   用户输入   │
└──────┬──────┘
       │ CLI 参数
       ▼
┌─────────────┐
│   cli.py    │ ──► 解析命令
└──────┬──────┘
       │ 调用 GitOps
       ▼
┌─────────────┐
│ git_ops.py  │ ──► 执行 git 操作，返回结果
└──────┬──────┘
       │ 结果 + 触发事件
       ▼
┌─────────────┐
│   fsm.py    │ ──► 状态转移验证，更新状态
└──────┬──────┘
       │ 新状态
       ▼
┌─────────────┐
│   cli.py    │ ──► 格式化输出
└─────────────┘
```

## 4. 状态定义

### 主仓库状态

| 状态 | 标识 | 含义 | 允许的下一步 |
|------|------|------|--------------|
| Dirty | M0 | 有变更未提交 | doc-check |
| CleanAndConsistent | M1 | 干净且一致 | submodule-sync, 修改文件 |
| Inconsistent | M2 | 配置不一致 | 手动修复 |
| Synced | M3 | 子模块已同步 | auto-commit |
| Committed | M4 | 变更已提交 | git push |

### 子模块状态

| 状态 | 标识 | 含义 |
|------|------|------|
| Behind | S0 | 落后远程 |
| UpToDate | S1 | 已同步 |
| Detached | S2 | 分离头指针 |

### 错误状态

| 状态 | 标识 | 含义 | 处理方式 |
|------|------|------|----------|
| NetworkError | E1 | 网络问题 | 等待重试或人工介入 |
| ConsistencyError | E2 | 一致性失败 | 手动修复 YAML/.gitmodules |
| DetachedHeadError | E3 | 分离头指针 | checkout 到分支 |
| PermissionError | E4 | 权限不足 | 检查文件权限 |

## 5. 转移规则

### 合法转移表

| 当前状态 | 事件 | 前置条件 | 结果状态 |
|----------|------|----------|----------|
| M0 | doc_check_ok | - | M1 |
| M0 | doc_check_fail | - | M2 |
| M1 | submodule_sync | - | M3 |
| M1 | edit | - | M0 |
| M2 | fix | - | M1 |
| M3 | auto_commit | - | M4 |
| M4 | push_ok | - | M1 |
| M4 | push_fail | - | E1 |

### 非法转移（需抛出异常）

| 当前状态 | 禁止事件 | 说明 |
|----------|----------|------|
| M0 | submodule_sync | 需先通过 doc-check |
| M0 | auto_commit | 需先通过 doc-check |
| M2 | submodule_sync | 需先修复一致性 |
| M2 | auto_commit | 需先修复一致性 |

## 6. 实现要点

### GitOps 类接口

```python
class GitOps:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
    
    def get_status(self) -> RepoStatus:
        """获取仓库状态"""
    
    def check_consistency(self, yaml_path: Path) -> bool:
        """检查 YAML 与 .gitmodules 一致性"""
    
    def sync_submodules(self, paths: list[str] = None) -> SyncResult:
        """同步子模块"""
    
    def commit_and_push(self, message: str) -> PushResult:
        """提交并推送"""
    
    def get_submodule_status(self) -> list[SubmoduleStatus]:
        """获取子模块状态"""
```

### StateMachine 类接口

```python
class StateMachine:
    def __init__(self, initial_state: RepoState):
        self.state = initial_state
    
    def can_transition(self, event: str) -> bool:
        """检查是否可以转移"""
    
    def transition(self, event: str) -> RepoState:
        """执行状态转移"""
    
    def get_allowed_events(self) -> list[str]:
        """获取当前状态允许的事件"""
```

## 7. 迁移策略

详见 [迁移步骤](./migration.md)

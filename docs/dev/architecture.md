# 架构设计

## 1. 架构原则

**极简**：用最少的代码解决实际问题，避免过度设计。

## 2. 模块结构

```
src/thera/src/thera/
├── cli.py              # 入口，解析命令
├── git_ops.py          # Git 操作封装
└── refresh.py           # refresh 命令实现
```

## 3. 职责划分

| 模块 | 职责 |
|------|------|
| cli.py | 解析命令行参数，调用 refresh |
| git_ops.py | 封装所有 git 操作 |
| refresh.py | 组合 git_ops 实现同步+提交+推送 |

## 4. refresh 命令流程

```
┌─────────────────────────────────────┐
│ 1. 检测子模块更新                    │
│    git submodule status             │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│ 2. 拉取最新                          │
│    git submodule update --remote    │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│ 3. 检查主仓库状态                     │
│    git status                       │
└─────────────────────────────────────┘
                │
        有变更？ ───否───► 完成
                │
               是
                ▼
┌─────────────────────────────────────┐
│ 4. 提交并推送                         │
│    git add .                         │
│    git commit -m "chore: sync"       │
│    git push                          │
└─────────────────────────────────────┘
```

## 5. GitOps 类

```python
class GitOps:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
    
    def get_submodule_status(self) -> list[SubmoduleStatus]:
        """获取子模块状态"""
    
    def update_submodule(self, path: str) -> bool:
        """更新单个子模块"""
    
    def get_status(self) -> RepoStatus:
        """获取主仓库状态"""
    
    def commit_and_push(self, message: str) -> PushResult:
        """提交并推送"""
```

## 6. 与旧架构对比

| 旧架构 | 新架构 |
|--------|--------|
| FSM + Workflow Engine | 简单函数 |
| M0-M4 状态机 | 无状态机 |
| doc-check → sync → commit | refresh 一步完成 |
| 范畴论工作流组合 | 顺序调用 |

## 7. 相关文档

- [工作流设计](./gitops/gitops-workflow.md)
- [Git 操作封装](./gitops/git-ops-design.md)

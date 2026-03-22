# Git 操作封装

## 概述

`git_ops.py` 封装所有 Git 操作，提供清晰的返回类型。

## 核心类

```python
class GitOps:
    """Git 操作封装"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
    
    def get_status(self) -> RepoStatus:
        """获取仓库状态"""
    
    def get_submodule_status(self) -> list[SubmoduleInfo]:
        """获取子模块状态"""
    
    def sync_submodules(self, paths: list[str] = None) -> SyncResult:
        """同步子模块"""
    
    def commit_and_push(self, message: str) -> PushResult:
        """提交并推送"""
```

## 数据类

| 类 | 说明 |
|----|------|
| `RepoStatus` | 仓库状态（是否干净、变更列表） |
| `SubmoduleInfo` | 子模块信息（路径、commit、是否落后） |
| `SyncResult` | 同步结果 |
| `PushResult` | 推送结果 |

## 相关文档

- [Git 操作封装详情](./git-ops-design.md)

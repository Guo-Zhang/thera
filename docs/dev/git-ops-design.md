# Git 操作层设计

## 1. 设计目标

1. **统一封装**：消除各模块重复的 `run_git()` 函数
2. **明确返回**：所有操作返回明确的结果，而非依赖退出码和 stderr
3. **可测试性**：操作逻辑与 CLI 解耦，便于单元测试

## 2. 数据类定义

### 2.1 仓库状态

```python
from dataclasses import dataclass
from enum import Enum, auto

class ChangeType(Enum):
    """变更类型"""
    NEW = auto()
    MODIFIED = auto()
    DELETED = auto()
    UNTRACKED = auto()

@dataclass
class FileChange:
    """文件变更"""
    path: str
    change_type: ChangeType
    type_prefix: str  # docs/code/config/meta/root

@dataclass
class RepoStatus:
    """仓库状态"""
    is_clean: bool
    changes: list[FileChange]
    submodule_changes: list[str]  # 有变更的子模块路径

@dataclass
class SubmoduleInfo:
    """子模块信息"""
    path: str
    local_commit: str
    remote_commit: str | None  # None 表示无法获取
    is_behind: bool
    is_detached: bool
```

### 2.2 操作结果

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class OperationResult:
    """操作结果基类"""
    success: bool
    message: str
    error: Optional[str] = None

@dataclass
class ConsistencyResult(OperationResult):
    """一致性检查结果"""
    is_consistent: bool
    missing_paths: list[str] = None
    mismatched_names: list[str] = None

@dataclass
class SyncResult(OperationResult):
    """同步结果"""
    synced_paths: list[str] = None
    failed_paths: list[str] = None

@dataclass
class PushResult(OperationResult):
    """推送结果"""
    commit_sha: Optional[str] = None
    remote_ref: Optional[str] = None
```

## 3. GitOps 类实现

### 3.1 类定义

```python
import subprocess
from pathlib import Path
from typing import Optional
import yaml

class GitOps:
    """Git 操作封装"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
    
    def run_git(self, args: list[str], capture: bool = True) -> tuple[str, str, int]:
        """执行 git 命令"""
        cmd = ["git", "-C", str(self.repo_root)] + args
        result = subprocess.run(cmd, capture_output=capture, text=True)
        stdout = result.stdout if capture else ""
        stderr = result.stderr if capture else ""
        return stdout, stderr, result.returncode
```

### 3.2 状态查询

```python
    def get_status(self) -> RepoStatus:
        """获取仓库状态"""
        stdout, _, code = self.run_git(["status", "--porcelain"])
        
        if code != 0 or not stdout.strip():
            return RepoStatus(is_clean=True, changes=[], submodule_changes=[])
        
        changes = []
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            status = line[:2].strip()
            file_path = line[3:].strip()
            
            # 解析变更类型
            if status.startswith("??"):
                change_type = ChangeType.UNTRACKED
            elif status.startswith("D"):
                change_type = ChangeType.DELETED
            elif status == "M" or status.startswith("M"):
                change_type = ChangeType.MODIFIED
            elif status == "A" or status.startswith("A"):
                change_type = ChangeType.NEW
            else:
                change_type = ChangeType.MODIFIED
            
            changes.append(FileChange(
                path=file_path,
                change_type=change_type,
                type_prefix=self._get_change_type(file_path)
            ))
        
        return RepoStatus(
            is_clean=len(changes) == 0,
            changes=changes,
            submodule_changes=[]
        )
    
    def _get_change_type(self, file_path: str) -> str:
        """根据文件路径识别变更类型"""
        if file_path.startswith("docs/"):
            return "docs"
        elif file_path.startswith("src/"):
            return "code"
        elif file_path in [".gitmodules", ".gitignore"]:
            return "config"
        elif file_path.startswith("meta/"):
            return "meta"
        else:
            return "root"
```

### 3.3 一致性检查

```python
    def check_consistency(self, yaml_path: Path) -> ConsistencyResult:
        """检查 YAML 与 .gitmodules 一致性"""
        # 1. 解析 YAML
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
        except Exception as e:
            return ConsistencyResult(
                success=False,
                is_consistent=False,
                message=f"无法读取 YAML: {e}",
                error=str(e)
            )
        
        yaml_paths = {item["path"] for item in data.get("submodules", [])}
        
        # 2. 解析 .gitmodules
        gitmodules_paths = self._get_gitmodules_paths()
        
        # 3. 比对
        missing_in_yaml = gitmodules_paths - yaml_paths
        missing_in_gitmodules = yaml_paths - gitmodules_paths
        
        if missing_in_yaml or missing_in_gitmodules:
            return ConsistencyResult(
                success=False,
                is_consistent=False,
                message="不一致",
                missing_paths=list(missing_in_yaml | missing_in_gitmodules)
            )
        
        # 4. 检查路径存在性
        missing_dirs = []
        for path in yaml_paths:
            if not (self.repo_root / path).exists():
                missing_dirs.append(path)
        
        if missing_dirs:
            return ConsistencyResult(
                success=False,
                is_consistent=False,
                message=f"缺失: {', '.join(missing_dirs)}",
                missing_paths=missing_dirs
            )
        
        return ConsistencyResult(
            success=True,
            is_consistent=True,
            message=f"{len(yaml_paths)} 个路径"
        )
    
    def _get_gitmodules_paths(self) -> set[str]:
        """解析 .gitmodules 获取路径"""
        paths = set()
        stdout, _, _ = self.run_git(["config", "--get-regexp", "^submodule\\..*\\.path$"])
        
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            _, path = line.split()
            paths.add(path)
        
        return paths
```

### 3.4 子模块同步

```python
    def get_submodule_status(self) -> list[SubmoduleInfo]:
        """获取子模块状态"""
        stdout, _, code = self.run_git(["submodule", "status"])
        
        if code != 0:
            return []
        
        results = []
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            
            status = parts[0]
            path = parts[1]
            
            is_behind = status.startswith("+")
            is_detached = status.startswith("U") or status.startswith("c")
            local_commit = status.lstrip("+")
            
            results.append(SubmoduleInfo(
                path=path,
                local_commit=local_commit[:7],
                remote_commit=None,  # status 不直接提供远程 commit
                is_behind=is_behind,
                is_detached=is_detached
            ))
        
        return results
    
    def sync_submodules(self, paths: list[str] = None) -> SyncResult:
        """同步子模块"""
        if paths:
            cmd = ["submodule", "update", "--remote", "--merge"] + paths
        else:
            cmd = ["submodule", "update", "--remote", "--merge"]
        
        stdout, stderr, code = self.run_git(cmd)
        
        if code != 0:
            return SyncResult(
                success=False,
                message="同步失败",
                error=stderr
            )
        
        synced = paths or ["all"]
        return SyncResult(
            success=True,
            message="同步完成",
            synced_paths=synced
        )
```

### 3.5 提交推送

```python
    def commit_and_push(self, message: str) -> PushResult:
        """提交并推送"""
        # 1. git add
        _, stderr, code = self.run_git(["add", "-A"])
        if code != 0:
            return PushResult(
                success=False,
                message="git add 失败",
                error=stderr
            )
        
        # 2. git commit
        stdout, stderr, code = self.run_git(["commit", "-m", message])
        
        if code != 0:
            if "nothing to commit" in stderr:
                return PushResult(
                    success=True,
                    message="无变更",
                    commit_sha=None
                )
            return PushResult(
                success=False,
                message="git commit 失败",
                error=stderr
            )
        
        # 3. 获取 commit SHA
        stdout, _, _ = self.run_git(["rev-parse", "HEAD"])
        commit_sha = stdout.strip()[:7]
        
        # 4. git push
        _, stderr, code = self.run_git(["push"])
        
        if code != 0:
            return PushResult(
                success=False,
                message="git push 失败",
                error=stderr,
                commit_sha=commit_sha
            )
        
        return PushResult(
            success=True,
            message="推送成功",
            commit_sha=commit_sha
        )
```

## 4. 使用示例

```python
from pathlib import Path
from thera.git_ops import GitOps

# 初始化
ops = GitOps(Path("/path/to/repo"))

# 检查一致性
result = ops.check_consistency(Path("meta/profile/submodules.yaml"))
print(f"一致性: {result.is_consistent}")

# 获取子模块状态
submodules = ops.get_submodule_status()
behind = [s for s in submodules if s.is_behind]
print(f"落后: {len(behind)} 个")

# 提交推送
result = ops.commit_and_push("[code] 修复 bug")
if result.success:
    print(f"提交: {result.commit_sha}")
else:
    print(f"失败: {result.error}")
```

## 5. 错误处理

| 错误类型 | Git 退出码 | 处理方式 |
|----------|------------|----------|
| 无变更 | 0 + "nothing to commit" | 返回 success=True, message="无变更" |
| 权限不足 | 128 + "Permission denied" | 返回 success=False, 提示检查权限 |
| 网络超时 | 128 + "Connection timed out" | 返回 success=False, 提示检查网络 |
| 子模块未初始化 | 128 + "not initialized" | 返回 success=False, 提示先初始化 |

## 6. 与状态机集成

```python
from thera.fsm import StateMachine, RepoState, Event
from thera.git_ops import GitOps

class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self, repo_root: Path):
        self.git_ops = GitOps(repo_root)
        self.machine = StateMachine(RepoState.DIRTY)
    
    def doc_check(self, yaml_path: Path) -> bool:
        """执行一致性检查"""
        result = self.git_ops.check_consistency(yaml_path)
        
        if result.is_consistent:
            self.machine.transition(Event.DOC_CHECK_OK)
        else:
            self.machine.transition(Event.DOC_CHECK_FAIL)
        
        return result.is_consistent
    
    def sync(self) -> bool:
        """同步子模块"""
        if Event.SUBMODULE_SYNC not in self.machine.get_allowed_events():
            raise IllegalTransitionError(
                self.machine.state,
                Event.SUBMODULE_SYNC
            )
        
        result = self.git_ops.sync_submodules()
        if result.success:
            self.machine.transition(Event.SUBMODULE_SYNC)
        
        return result.success
    
    def commit(self, message: str) -> bool:
        """提交并推送"""
        if Event.AUTO_COMMIT not in self.machine.get_allowed_events():
            raise IllegalTransitionError(
                self.machine.state,
                Event.AUTO_COMMIT
            )
        
        result = self.git_ops.commit_and_push(message)
        
        if result.success:
            self.machine.transition(Event.PUSH_OK)
        else:
            self.machine.transition(Event.PUSH_FAIL)
        
        return result.success
```

"""
Git 操作封装层

统一封装所有 git 操作，消除重复代码，返回明确的结果类型。
"""

import subprocess
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Optional

import yaml


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
    type_prefix: str


@dataclass
class RepoStatus:
    """仓库状态"""

    is_clean: bool
    changes: list[FileChange]


@dataclass
class SubmoduleInfo:
    """子模块信息"""

    path: str
    local_commit: str
    is_behind: bool
    is_detached: bool


@dataclass
class OperationResult:
    """操作结果基类"""

    success: bool
    message: str
    error: Optional[str] = None


@dataclass
class ConsistencyResult:
    """一致性检查结果"""

    success: bool
    message: str
    is_consistent: bool
    error: Optional[str] = None
    missing_paths: Optional[list[str]] = None


@dataclass
class SyncResult(OperationResult):
    """同步结果"""

    synced_paths: Optional[list[str]] = None


@dataclass
class PushResult(OperationResult):
    """推送结果"""

    commit_sha: Optional[str] = None


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

    def get_status(self) -> RepoStatus:
        """获取仓库状态"""
        stdout, _, code = self.run_git(["status", "--porcelain"])

        if code != 0 or not stdout.strip():
            return RepoStatus(is_clean=True, changes=[])

        changes = []
        for line in stdout.split("\n"):
            if not line or not line.strip():
                continue
            status = line[:2]
            file_path = line[3:].strip()

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

            changes.append(
                FileChange(
                    path=file_path,
                    change_type=change_type,
                    type_prefix=self._get_change_type(file_path),
                )
            )

        return RepoStatus(is_clean=len(changes) == 0, changes=changes)

    def get_submodule_status(self) -> list[SubmoduleInfo]:
        """获取子模块状态"""
        stdout, _, code = self.run_git(["submodule", "status"])

        if code != 0 or not stdout.strip():
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
            is_detached = status.startswith("u") or status.startswith("c")
            local_commit = status.lstrip("+")[:7]

            results.append(
                SubmoduleInfo(
                    path=path,
                    local_commit=local_commit,
                    is_behind=is_behind,
                    is_detached=is_detached,
                )
            )

        return results

    def _get_gitmodules_paths(self) -> dict[str, str]:
        """解析 .gitmodules 获取路径"""
        paths = {}
        stdout, _, _ = self.run_git(
            ["config", "--get-regexp", r"^submodule\..*\.path$"]
        )

        for line in stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                key, path = parts
                paths[key] = path

        return paths

    def check_consistency(self, yaml_path: Path) -> ConsistencyResult:
        """检查 YAML 与 .gitmodules 一致性"""
        yaml_full = self.repo_root / yaml_path
        if not yaml_full.exists():
            return ConsistencyResult(
                success=False,
                is_consistent=False,
                message="YAML 事实源不存在",
                error="file not found",
            )

        try:
            with open(yaml_full) as f:
                data = yaml.safe_load(f)
            yaml_modules = data.get("submodules", []) if data else []
        except Exception as e:
            return ConsistencyResult(
                success=False,
                is_consistent=False,
                message=f"无法读取 YAML: {e}",
                error=str(e),
            )

        git_modules = self._get_gitmodules_paths()
        git_paths = {v for v in git_modules.values()}
        yaml_paths = {m["path"] for m in yaml_modules}

        missing_in_yaml = git_paths - yaml_paths
        missing_in_git = yaml_paths - git_paths

        if missing_in_yaml or missing_in_git:
            missing = list(missing_in_yaml | missing_in_git)
            return ConsistencyResult(
                success=False,
                is_consistent=False,
                message=f"不一致，缺失: {', '.join(missing)}",
                missing_paths=missing,
            )

        missing_dirs = []
        for path in yaml_paths:
            if not (self.repo_root / path).exists():
                missing_dirs.append(path)

        if missing_dirs:
            return ConsistencyResult(
                success=False,
                is_consistent=False,
                message=f"路径缺失: {', '.join(missing_dirs)}",
                missing_paths=missing_dirs,
            )

        return ConsistencyResult(
            success=True,
            is_consistent=True,
            message=f"{len(yaml_paths)} 个路径",
        )

    def sync_submodules(self, paths: Optional[list[str]] = None) -> SyncResult:
        """同步子模块"""
        if paths:
            cmd = ["submodule", "update", "--remote", "--merge"] + paths
        else:
            cmd = ["submodule", "update", "--remote", "--merge"]

        _, stderr, code = self.run_git(cmd)

        if code != 0:
            return SyncResult(
                success=False,
                message="同步失败",
                error=stderr,
            )

        return SyncResult(
            success=True,
            message="同步完成",
            synced_paths=paths or ["all"],
        )

    def commit_and_push(self, message: str) -> PushResult:
        """提交并推送"""
        _, stderr, code = self.run_git(["add", "-A"])
        if code != 0:
            return PushResult(
                success=False,
                message="git add 失败",
                error=stderr,
            )

        _, stderr, code = self.run_git(["commit", "-m", message])

        if code != 0:
            if stderr and "nothing to commit" in stderr:
                return PushResult(
                    success=True,
                    message="无变更",
                    commit_sha=None,
                )
            return PushResult(
                success=False,
                message="git commit 失败",
                error=stderr,
            )

        stdout, _, _ = self.run_git(["rev-parse", "HEAD"])
        commit_sha = stdout.strip()[:7]

        _, stderr, code = self.run_git(["push"])

        if code != 0:
            return PushResult(
                success=False,
                message="git push 失败",
                error=stderr,
                commit_sha=commit_sha,
            )

        return PushResult(
            success=True,
            message="推送成功",
            commit_sha=commit_sha,
        )

"""
Refresh 命令

同步子模块并提交推送主仓库。
"""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from subprocess import TimeoutExpired
from typing import Optional

from thera.git_ops import GitOps, SubmoduleInfo


@dataclass
class RefreshResult:
    """refresh 操作结果"""

    success: bool
    message: str
    error: Optional[str] = None
    updated_submodules: list[str] = field(default_factory=list)
    commit_sha: Optional[str] = None
    dry_run: bool = False


SUBMODULE_PATHS = [
    "docs/archive",
    "docs/bylaw",
    "docs/essay",
    "docs/handbook",
    "docs/history",
    "docs/journal",
    "docs/library",
    "docs/paper",
    "docs/profile",
    "docs/report",
    "docs/roadmap",
    "docs/specification",
    "docs/tutorial",
    "docs/usercase",
    "packages/data",
    "packages/devops",
    "src/qtadmin",
    "src/thera",
]

SUBMODULE_NAMES = {
    "archive": "docs/archive",
    "bylaw": "docs/bylaw",
    "essay": "docs/essay",
    "handbook": "docs/handbook",
    "history": "docs/history",
    "journal": "docs/journal",
    "library": "docs/library",
    "paper": "docs/paper",
    "profile": "docs/profile",
    "report": "docs/report",
    "roadmap": "docs/roadmap",
    "specification": "docs/specification",
    "tutorial": "docs/tutorial",
    "usercase": "docs/usercase",
    "data": "packages/data",
    "devops": "packages/devops",
    "qtadmin": "src/qtadmin",
    "thera": "src/thera",
}


def _get_submodule_paths(submodule: str) -> list[str]:
    """根据子模块名获取完整路径"""
    if submodule in SUBMODULE_NAMES:
        return [SUBMODULE_NAMES[submodule]]

    # 尝试直接匹配路径
    for path in SUBMODULE_PATHS:
        if path.endswith(f"/{submodule}") or path == submodule:
            return [path]

    return []


def refresh(
    repo_root: Path, dry_run: bool = False, submodule: str = None
) -> RefreshResult:
    """
    同步子模块并提交推送主仓库。

    流程：
    1. 检测子模块内部是否有未提交的变更
    2. Fetch 子模块远程
    3. 检测子模块远程更新
    4. 拉取最新
    5. 提交并推送主仓库变更

    Args:
        repo_root: 仓库根目录
        dry_run: 预览模式，不执行实际变更
        submodule: 指定子模块名（如 journal, archive）。不指定则同步所有
    """
    dirty_submodules = _get_dirty_submodules(repo_root)
    if dirty_submodules:
        return RefreshResult(
            success=False,
            message="子模块有未提交的变更",
            error=f"请先在子模块中提交: {', '.join(dirty_submodules)}",
        )

    _fetch_submodules(repo_root, submodule=submodule)

    updated_submodules = []
    submodule_status = _get_submodules_behind_remote(repo_root, submodule=submodule)

    for sm in submodule_status:
        if dry_run:
            updated_submodules.append(sm.path)
        else:
            ops = GitOps(repo_root)
            result = ops.sync_submodules([sm.path])
            if result.success:
                updated_submodules.append(sm.path)

    ops = GitOps(repo_root)
    status = ops.get_status()

    if not status.is_clean:
        if dry_run:
            return RefreshResult(
                success=True,
                dry_run=True,
                message=f"将提交 {len(status.changes)} 个变更",
                updated_submodules=updated_submodules,
            )

        commit_message = "chore(submodule): sync submodules"
        result = ops.commit_and_push(commit_message)

        if result.success:
            return RefreshResult(
                success=True,
                message="已提交并推送",
                updated_submodules=updated_submodules,
                commit_sha=result.commit_sha,
            )
        else:
            return RefreshResult(
                success=False,
                message="提交推送失败",
                error=result.error,
                updated_submodules=updated_submodules,
            )

    if updated_submodules:
        if dry_run:
            return RefreshResult(
                success=True,
                dry_run=True,
                message=f"将更新 {len(updated_submodules)} 个子模块",
                updated_submodules=updated_submodules,
            )
        return RefreshResult(
            success=True,
            message="子模块已更新",
            updated_submodules=updated_submodules,
        )

    return RefreshResult(
        success=True,
        message="已是最新",
        updated_submodules=[],
    )


def _fetch_submodules(repo_root: Path, submodule: str = None) -> None:
    """Fetch 子模块的远程"""
    paths = _get_submodule_paths(submodule) if submodule else SUBMODULE_PATHS

    for path in paths:
        full_path = repo_root / path
        if not full_path.exists():
            continue
        try:
            subprocess.run(
                ["git", "-C", str(full_path), "fetch", "origin"],
                capture_output=True,
                timeout=10,
            )
        except TimeoutExpired:
            pass


def _get_submodules_behind_remote(
    repo_root: Path, submodule: str = None
) -> list[SubmoduleInfo]:
    """
    获取落后于远程的子模块列表。

    比较本地 HEAD 和 origin/main，返回落后的子模块。

    Args:
        submodule: 指定子模块名（如 journal）
    """
    paths = _get_submodule_paths(submodule) if submodule else SUBMODULE_PATHS
    behind = []

    for path in paths:
        full_path = repo_root / path
        if not full_path.exists():
            continue

        try:
            result = subprocess.run(
                ["git", "-C", str(full_path), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            local_head = result.stdout.strip()

            result = subprocess.run(
                ["git", "-C", str(full_path), "rev-parse", "origin/main"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                continue
            remote_head = result.stdout.strip()

            if local_head != remote_head:
                behind.append(
                    SubmoduleInfo(
                        path=path,
                        local_commit=local_head[:7],
                        is_behind=True,
                        is_detached=False,
                    )
                )
        except TimeoutExpired:
            pass

    return behind


def _get_dirty_submodules(repo_root: Path) -> list[str]:
    """
    检查所有子模块是否有内部未提交的变更。

    Returns:
        有脏状态的子模块路径列表
    """
    dirty = []

    for path in SUBMODULE_PATHS:
        full_path = repo_root / path
        if not full_path.exists():
            continue

        try:
            result = subprocess.run(
                ["git", "-C", str(full_path), "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.stdout.strip():
                dirty.append(path)
        except TimeoutExpired:
            pass

    return dirty


def get_submodule_updates(repo_root: Path) -> list[SubmoduleInfo]:
    """获取需要更新的子模块列表"""
    _fetch_submodules(repo_root)
    return _get_submodules_behind_remote(repo_root)

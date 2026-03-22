"""
Refresh 命令

同步子模块并提交推送主仓库。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from thera.git_ops import GitOps, PushResult, SubmoduleInfo


@dataclass
class RefreshResult:
    """refresh 操作结果"""

    success: bool
    message: str
    error: Optional[str] = None
    updated_submodules: list[str] = field(default_factory=list)
    commit_sha: Optional[str] = None
    dry_run: bool = False


def refresh(repo_root: Path, dry_run: bool = False) -> RefreshResult:
    """
    同步子模块并提交推送主仓库。

    流程：
    1. 检测子模块更新
    2. 拉取最新
    3. 检查主仓库变更（排除子模块脏状态）
    4. 提交并推送（仅当有有效变更时）
    """
    ops = GitOps(repo_root)
    updated_submodules = []

    submodule_status = ops.get_submodule_status()

    for sm in submodule_status:
        if sm.is_behind:
            if dry_run:
                updated_submodules.append(sm.path)
            else:
                result = ops.sync_submodules([sm.path])
                if result.success:
                    updated_submodules.append(sm.path)

    status = ops.get_status()

    if not status.is_clean:
        dirty_submodules = _get_dirty_submodules(status)
        has_valid_changes = any(c.path not in dirty_submodules for c in status.changes)

        if dirty_submodules and not has_valid_changes:
            if dry_run:
                return RefreshResult(
                    success=True,
                    dry_run=True,
                    message="子模块有未提交的变更，无法更新父仓库指针",
                    updated_submodules=updated_submodules,
                )
            return RefreshResult(
                success=False,
                message="子模块有未提交的变更",
                error=f"请先提交子模块变更: {', '.join(dirty_submodules)}",
                updated_submodules=updated_submodules,
            )

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


def _get_dirty_submodules(status) -> list[str]:
    """获取有脏状态的子模块路径"""
    dirty = []
    for change in status.changes:
        if _is_submodule_path(change.path):
            dirty.append(change.path)
    return dirty


def _is_submodule_path(path: str) -> bool:
    """检查路径是否是子模块"""
    submodule_paths = [
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
    return path in submodule_paths


def get_submodule_updates(repo_root: Path) -> list[SubmoduleInfo]:
    """获取需要更新的子模块列表"""
    ops = GitOps(repo_root)
    return [sm for sm in ops.get_submodule_status() if sm.is_behind]

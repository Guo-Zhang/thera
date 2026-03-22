"""
Refresh 命令

同步子模块并提交推送主仓库。
"""

from dataclasses import dataclass, field
from pathlib import Path
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


def refresh(repo_root: Path, dry_run: bool = False) -> RefreshResult:
    """
    同步子模块并提交推送主仓库。

    流程：
    1. 检测子模块更新
    2. 拉取最新
    3. 提交并推送主仓库变更
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


def get_submodule_updates(repo_root: Path) -> list[SubmoduleInfo]:
    """获取需要更新的子模块列表"""
    ops = GitOps(repo_root)
    return [sm for sm in ops.get_submodule_status() if sm.is_behind]

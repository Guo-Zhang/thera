"""
工作流引擎模块

基于状态机的工作流编排，支持标准工作流和自定义工作流。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from thera.fsm import (
    ErrorState,
    Event,
    IllegalTransitionError,
    RepoState,
    StateMachine,
)
from thera.git_ops import (
    ConsistencyResult,
    GitOps,
    PushResult,
    SyncResult,
)


class ConvergenceStrategy(ABC):
    """收敛策略基类"""

    @abstractmethod
    def should_reconcile(self, submodule: str, is_behind: bool) -> bool:
        """判断是否应该自动收敛"""
        pass


class AutoStrategy(ConvergenceStrategy):
    """自动策略：自动修复"""

    def should_reconcile(self, submodule: str, is_behind: bool) -> bool:
        return True


class ManualStrategy(ConvergenceStrategy):
    """手动策略：需要人工确认"""

    def should_reconcile(self, submodule: str, is_behind: bool) -> bool:
        return False


class HybridStrategy(ConvergenceStrategy):
    """混合策略"""

    def should_reconcile(self, submodule: str, is_behind: bool) -> bool:
        return not is_behind


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    success: bool
    message: str
    new_state: Optional[RepoState] = None
    error: Optional[ErrorState] = None


class WorkflowEngine:
    """工作流引擎"""

    def __init__(
        self,
        repo_root: Path,
        strategy: Optional[ConvergenceStrategy] = None,
    ):
        self.repo_root = repo_root
        self.git_ops = GitOps(repo_root)
        self.machine = StateMachine()
        self.strategy = strategy or AutoStrategy()

    def doc_check(self, yaml_path: Path) -> ConsistencyResult:
        """执行一致性检查"""
        result = self.git_ops.check_consistency(yaml_path)

        if result.is_consistent:
            self.machine.transition(Event.DOC_CHECK_OK)
        else:
            self.machine.transition(Event.DOC_CHECK_FAIL)

        return result

    def sync_submodules(
        self, paths: Optional[list[str]] = None
    ) -> SyncResult:
        """同步子模块"""
        if not self.machine.can_transition(Event.SUBMODULE_SYNC):
            return SyncResult(
                success=False,
                message=f"当前状态 {self.machine.state.name} 不允许同步",
                error="illegal state transition",
            )

        result = self.git_ops.sync_submodules(paths)

        if result.success:
            self.machine.transition(Event.SUBMODULE_SYNC)

        return result

    def commit_and_push(self, message: str) -> PushResult:
        """提交并推送"""
        if self.machine.state == RepoState.SYNCED:
            self.machine.transition(Event.AUTO_COMMIT)
        elif self.machine.state != RepoState.COMMITTED:
            if not self.machine.can_transition(Event.AUTO_COMMIT):
                return PushResult(
                    success=False,
                    message=f"当前状态 {self.machine.state.name} 不允许提交",
                    error="illegal state transition",
                )
            self.machine.transition(Event.AUTO_COMMIT)

        result = self.git_ops.commit_and_push(message)

        if result.success:
            self.machine.transition(Event.PUSH_OK)
        else:
            self.machine.transition(Event.PUSH_FAIL)

        return result

    def run_standard_workflow(
        self, yaml_path: Path, commit_message: Optional[str] = None
    ) -> WorkflowResult:
        """运行标准工作流：doc-check → sync → commit"""
        try:
            doc_result = self.doc_check(yaml_path)
            if not doc_result.is_consistent:
                return WorkflowResult(
                    success=False,
                    message=f"一致性检查失败: {doc_result.message}",
                    new_state=self.machine.state,
                )

            sync_result = self.sync_submodules()
            if not sync_result.success:
                return WorkflowResult(
                    success=False,
                    message=f"子模块同步失败: {sync_result.message}",
                    new_state=self.machine.state,
                )

            if commit_message is None:
                commit_message = "[sync] auto commit from workflow"

            push_result = self.commit_and_push(commit_message)
            if not push_result.success:
                return WorkflowResult(
                    success=False,
                    message=f"提交推送失败: {push_result.message}",
                    new_state=self.machine.state,
                    error=self.machine.error,
                )

            return WorkflowResult(
                success=True,
                message="工作流执行成功",
                new_state=self.machine.state,
            )

        except IllegalTransitionError as e:
            return WorkflowResult(
                success=False,
                message=str(e),
                new_state=self.machine.state,
            )

    def append_journal(self, results: list[dict]) -> None:
        """追加日志到 meta/journal/YYYY-MM-DD.md"""
        today = datetime.now().strftime("%Y-%m-%d")
        journal_path = self.repo_root / "meta" / "journal" / f"{today}.md"
        now = datetime.now().strftime("%H:%M")

        lines = []
        for result in results:
            status = "OK" if result.get("success") else "FAIL"
            repo = result.get("repo", "main")
            types_str = result.get("types", "")
            lines.append(f"- {now} {status} {repo}: {types_str}")

        if lines:
            with open(journal_path, "a") as f:
                f.write("\n" + "\n".join(lines))

    def get_state(self) -> RepoState:
        """获取当前状态"""
        return self.machine.state

    def get_allowed_events(self) -> list[Event]:
        """获取当前允许的事件"""
        return self.machine.get_allowed_events()

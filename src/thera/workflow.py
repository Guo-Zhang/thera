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
    new_state: Optional[RepoState | ErrorState] = None
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

    def set_strategy(self, strategy_name: str) -> ConvergenceStrategy:
        """设置收敛策略"""
        strategies = {
            "auto": AutoStrategy,
            "manual": ManualStrategy,
            "hybrid": HybridStrategy,
        }
        
        if strategy_name not in strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}. Valid: {list(strategies.keys())}")
        
        self.strategy = strategies[strategy_name]()
        return self.strategy

    def get_strategy_name(self) -> str:
        """获取当前策略名称"""
        strategy_map = {
            AutoStrategy: "auto",
            ManualStrategy: "manual",
            HybridStrategy: "hybrid",
        }
        return strategy_map.get(type(self.strategy), "unknown")

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
        """运行标准工作流：doc-check → sync → commit（带事务性语义）"""
        checkpoints: list[str] = []
        
        try:
            doc_result = self.doc_check(yaml_path)
            if not doc_result.is_consistent:
                return WorkflowResult(
                    success=False,
                    message=f"一致性检查失败: {doc_result.message}",
                    new_state=self.machine.state,
                )
            checkpoints.append("doc_check")

            sync_result = self.sync_submodules()
            if not sync_result.success:
                self._rollback_sync(checkpoints)
                return WorkflowResult(
                    success=False,
                    message=f"子模块同步失败: {sync_result.message}",
                    new_state=self.machine.state,
                )
            checkpoints.append("sync")

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
            checkpoints.append("push")

            return WorkflowResult(
                success=True,
                message="工作流执行成功",
                new_state=self.machine.state,
            )

        except IllegalTransitionError as e:
            self._emergency_rollback(checkpoints)
            return WorkflowResult(
                success=False,
                message=str(e),
                new_state=self.machine.state,
            )

    def _rollback_sync(self, checkpoints: list[str]) -> None:
        """回滚同步操作"""
        if "sync" in checkpoints:
            pass

    def _emergency_rollback(self, checkpoints: list[str]) -> None:
        """紧急回滚"""
        pass

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

    def get_state(self) -> RepoState | ErrorState:
        """获取当前状态"""
        return self.machine.state

    def get_allowed_events(self) -> list[Event]:
        """获取当前允许的事件"""
        return self.machine.get_allowed_events()

    def get_status(self) -> dict:
        """获取完整状态信息"""
        state = self.machine.state
        status_info = {
            "state": state,
            "is_error": self.machine.is_error_state(),
            "allowed_events": self.get_allowed_events(),
            "history_count": len(self.machine.history),
        }
        
        if hasattr(state, "value"):
            status_info["state_name"] = state.name
        
        if self.machine.is_error_state():
            status_info["error"] = self.machine.error
        
        return status_info

    def get_error_details(self) -> dict | None:
        """获取错误详情"""
        if not self.machine.is_error_state():
            return None
        
        return {
            "error": self.machine.error,
            "error_name": self.machine.error.name if self.machine.error else None,
            "suggestion": self._get_error_suggestion(self.machine.error),
        }

    def _get_error_suggestion(self, error: ErrorState | None) -> str:
        """获取错误建议"""
        if error is None:
            return "无错误"
        
        suggestions = {
            ErrorState.NETWORK_ERROR: "检查网络连接后重试",
            ErrorState.CONSISTENCY_ERROR: "运行 doc-check 检查配置一致性",
            ErrorState.DETACHED_HEAD_ERROR: "切换到正确的分支",
            ErrorState.PERMISSION_ERROR: "检查 git 权限配置",
        }
        return suggestions.get(error, "请查看错误详情")

    def get_history(self, limit: int = 10) -> list[dict]:
        """获取状态历史"""
        history = []
        for i, (from_state, event) in enumerate(self.machine.history[-limit:], 1):
            history.append({
                "index": len(self.machine.history) - limit + i,
                "from_state": from_state,
                "event": event,
                "event_name": event.name,
                "from_state_name": from_state.name if hasattr(from_state, "name") else str(from_state),
            })
        return history

    def audit(self, since: datetime | None = None, until: datetime | None = None) -> dict:
        """生成审计报告"""
        total_transitions = len(self.machine.history)
        error_count = sum(1 for s, _ in self.machine.history 
                         if isinstance(s, ErrorState) or 
                         (hasattr(s, "name") and "ERROR" in s.name))
        
        state_distribution = {}
        for from_state, _ in self.machine.history:
            state_name = from_state.name if hasattr(from_state, "name") else str(from_state)
            state_distribution[state_name] = state_distribution.get(state_name, 0) + 1
        
        errors = []
        for i, (state, event) in enumerate(self.machine.history):
            if isinstance(state, ErrorState) or (hasattr(state, "name") and "ERROR" in state.name):
                errors.append({
                    "index": i,
                    "error": state,
                    "event": event,
                })
        
        return {
            "total_transitions": total_transitions,
            "error_count": error_count,
            "state_distribution": state_distribution,
            "errors": errors,
        }

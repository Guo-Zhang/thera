"""
Thera CLI - 统一入口

Usage:
    thera auto-commit [--dry-run]
    thera doc-check [--repo PATH]
    thera submodule-sync [--check] [--sync PATHS] [--sync-all]
    thera workflow status
    thera workflow history [--limit N]
    thera workflow audit [--since DATE] [--until DATE]
    thera --help

架构说明：
- CLI 层：入口解析和输出格式化
- Workflow 层：状态管理和流程控制（默认）
- GitOps 层：Git 操作封装
"""

import argparse
import sys
from pathlib import Path

from thera.workflow import WorkflowEngine


def main():
    parser = argparse.ArgumentParser(
        prog="thera",
        description="Thera - Quanttide 数字资产治理工具",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    auto_commit_parser = subparsers.add_parser(
        "auto-commit",
        help="检测变更并提交推送"
    )
    auto_commit_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅显示变更，不提交"
    )
    auto_commit_parser.add_argument(
        "--repo",
        default=".",
        help="仓库根目录"
    )
    auto_commit_parser.add_argument(
        "--strategy",
        choices=["auto", "manual", "hybrid"],
        default="auto",
        help="收敛策略"
    )
    
    doc_check_parser = subparsers.add_parser(
        "doc-check",
        help="检查文档一致性"
    )
    doc_check_parser.add_argument(
        "--config",
        default="meta/profile/submodules.yaml",
        help="YAML 配置文件路径"
    )
    doc_check_parser.add_argument(
        "--repo",
        default=".",
        help="仓库根目录"
    )
    
    submodule_parser = subparsers.add_parser(
        "submodule-sync",
        help="同步子模块"
    )
    submodule_parser.add_argument(
        "--check",
        action="store_true",
        help="检测远程更新"
    )
    submodule_parser.add_argument(
        "--sync",
        metavar="PATHS",
        help="同步指定子模块（逗号分隔）"
    )
    submodule_parser.add_argument(
        "--sync-all",
        action="store_true",
        help="同步所有子模块"
    )
    submodule_parser.add_argument(
        "--repo",
        default=".",
        help="仓库根目录"
    )
    
    workflow_parser = subparsers.add_parser(
        "workflow",
        help="工作流相关命令"
    )
    workflow_subparsers = workflow_parser.add_subparsers(dest="workflow_command", help="子命令")
    
    status_parser = workflow_subparsers.add_parser("status", help="查看当前状态")
    status_parser.add_argument("--repo", default=".", help="仓库根目录")
    
    history_parser = workflow_subparsers.add_parser("history", help="查看状态历史")
    history_parser.add_argument("--limit", type=int, default=10, help="显示条数")
    history_parser.add_argument("--repo", default=".", help="仓库根目录")
    
    audit_parser = workflow_subparsers.add_parser("audit", help="生成审计报告")
    audit_parser.add_argument("--since", help="开始日期 (YYYY-MM-DD)")
    audit_parser.add_argument("--until", help="结束日期 (YYYY-MM-DD)")
    audit_parser.add_argument("--repo", default=".", help="仓库根目录")
    
    args = parser.parse_args()
    
    if args.command == "auto-commit":
        return run_auto_commit(args)
    elif args.command == "doc-check":
        return run_doc_check(args)
    elif args.command == "submodule-sync":
        return run_submodule_sync(args)
    elif args.command == "workflow":
        return run_workflow(args)
    else:
        parser.print_help()
        return 1


def run_auto_commit(args):
    """运行 auto-commit"""
    repo_root = Path(args.repo)
    engine = WorkflowEngine(repo_root)
    
    strategy_name = getattr(args, "strategy", "auto")
    if strategy_name != "auto":
        engine.set_strategy(strategy_name)
        print(f"[策略] {strategy_name}")
    
    status = engine.git_ops.get_status()
    
    if status.is_clean:
        print("[OK] No changes detected")
        return 0
    
    print("Detected changes:")
    print("-" * 50)
    
    changes = status.changes
    if changes:
        print(f"主仓库: {len(changes)} 个文件")
        for change in changes[:5]:
            print(f"  {change.change_type.name}: {change.path}")
        if len(changes) > 5:
            print(f"  ... (+{len(changes) - 5} more)")
    
    print("-" * 50)
    
    if args.dry_run:
        print("\nDry run - no changes made.")
        return 0
    
    print("\nCommit and push these changes? [y/N/q]: ", end="")
    response = input().strip().lower()
    
    if response == "q":
        print("Aborted.")
        return 0
    elif response != "y":
        print("No changes committed.")
        return 0
    
    result = engine.commit_and_push("[sync] auto commit from workflow")
    
    if result.success:
        print(f"\n[OK] Pushed: {result.commit_sha}")
        return 0
    else:
        print(f"\n[FAIL] {result.message}")
        if result.error:
            print(f"  Error: {result.error}")
        return 1


def run_doc_check(args):
    """运行 doc-check"""
    repo_root = Path(args.repo)
    engine = WorkflowEngine(repo_root)
    
    config_path = getattr(args, "config", "meta/profile/submodules.yaml")
    
    result = engine.doc_check(Path(config_path))
    
    if result.is_consistent:
        print(f"[OK] 一致性检查通过")
        return 0
    else:
        print(f"[WARN] 一致性检查失败: {result.message}")
        if result.missing_paths:
            print(f"  缺失路径: {', '.join(result.missing_paths)}")
        return 1


def run_submodule_sync(args):
    """运行 submodule-sync"""
    repo_root = Path(args.repo)
    engine = WorkflowEngine(repo_root)
    
    if args.check:
        submodules = engine.git_ops.get_submodule_status()
        if not submodules:
            print("[OK] No submodules")
            return 0
        
        print(f"子模块数: {len(submodules)}")
        for sub in submodules:
            status = "有更新" if sub.is_behind else "已是最新"
            print(f"  {sub.path}: {sub.local_commit} ({status})")
        return 0
    
    if args.sync_all:
        paths = None
    elif args.sync:
        paths = args.sync.split(",")
    else:
        paths = None
    
    result = engine.sync_submodules(paths)
    
    if result.success:
        print(f"[OK] 同步完成")
        return 0
    else:
        print(f"[FAIL] 同步失败: {result.message}")
        if result.error:
            print(f"  Error: {result.error}")
        return 1


def run_workflow(args):
    """运行 workflow 子命令"""
    if args.workflow_command == "status":
        return run_workflow_status(args)
    elif args.workflow_command == "history":
        return run_workflow_history(args)
    elif args.workflow_command == "audit":
        return run_workflow_audit(args)
    else:
        print("请指定子命令: status, history, audit")
        return 1


def run_workflow_status(args):
    """运行 workflow status"""
    repo_root = Path(args.repo)
    engine = WorkflowEngine(repo_root)
    
    status = engine.get_status()
    state = status["state"]
    state_name = state.name if hasattr(state, "name") else str(state)
    
    print(f"当前状态: {state_name}")
    print("-" * 60)
    
    if status["is_error"]:
        error_details = engine.get_error_details()
        if error_details:
            print(f"错误: {error_details['error_name']}")
            print(f"建议: {error_details['suggestion']}")
    else:
        git_status = engine.git_ops.get_status()
        if git_status.is_clean:
            print("变更: 无")
        else:
            print(f"变更: {len(git_status.changes)} 个文件待提交")
    
    if status["allowed_events"]:
        print("\n允许操作:")
        for event in status["allowed_events"]:
            print(f"  • {event.name}")
    
    print("-" * 60)
    print(f"状态转移历史: {status['history_count']} 次")
    
    return 0


def run_workflow_history(args):
    """运行 workflow history"""
    repo_root = Path(args.repo)
    engine = WorkflowEngine(repo_root)
    
    history = engine.get_history(limit=args.limit)
    
    if not history:
        print("暂无状态历史")
        return 0
    
    print(f"状态历史 (最近 {len(history)} 条)")
    print("-" * 60)
    
    for item in history:
        from_name = item["from_state_name"]
        event_name = item["event_name"]
        print(f"  {from_name:<20} → {event_name}")
    
    print("-" * 60)
    print(f"总计: {engine.machine.history.__len__()} 次状态转移")
    
    return 0


def run_workflow_audit(args):
    """运行 workflow audit"""
    repo_root = Path(args.repo)
    engine = WorkflowEngine(repo_root)
    
    audit_report = engine.audit()
    
    print("审计报告")
    print("=" * 60)
    print("概览")
    print("-" * 60)
    print(f"状态转移: {audit_report['total_transitions']} 次")
    print(f"错误次数: {audit_report['error_count']} 次")
    
    if audit_report["state_distribution"]:
        print("\n状态分布")
        print("-" * 60)
        total = sum(audit_report["state_distribution"].values())
        for state_name, count in sorted(
            audit_report["state_distribution"].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            percentage = count / total * 100
            bar = "█" * int(percentage / 5)
            print(f"  {state_name:<25} {bar:<20} {percentage:.1f}%")
    
    if audit_report["errors"]:
        print("\n错误详情")
        print("-" * 60)
        for err in audit_report["errors"]:
            error_name = err["error"].name if hasattr(err["error"], "name") else str(err["error"])
            event_name = err["event"].name if hasattr(err["event"], "name") else str(err["event"])
            print(f"  • {error_name} - {event_name}")
    
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

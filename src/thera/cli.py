"""
Thera CLI - 统一入口

Usage:
    thera auto-commit [--dry-run]
    thera doc-check [--repo PATH]
    thera submodule-sync [--check] [--sync PATHS] [--sync-all]
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
    
    args = parser.parse_args()
    
    if args.command == "auto-commit":
        return run_auto_commit(args)
    elif args.command == "doc-check":
        return run_doc_check(args)
    elif args.command == "submodule-sync":
        return run_submodule_sync(args)
    else:
        parser.print_help()
        return 1


def run_auto_commit(args):
    """运行 auto-commit"""
    repo_root = Path(args.repo)
    engine = WorkflowEngine(repo_root)
    
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


if __name__ == "__main__":
    sys.exit(main())

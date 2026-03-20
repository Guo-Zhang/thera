"""
Thera CLI - 统一入口

Usage:
    thera auto-commit [--dry-run] [--new-engine]
    thera doc-check [--repo PATH] [--new-engine]
    thera submodule-sync [--check] [--sync PATHS] [--sync-all] [--new-engine]
    thera --help

Options:
    --new-engine    使用新的领域层引擎（影子模式）
"""

import argparse
import sys
from pathlib import Path

from thera import auto_commit
from thera import doc_check
from thera import submodule_sync


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
        "--new-engine",
        action="store_true",
        help="使用新的领域层引擎（影子模式）"
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
    doc_check_parser.add_argument(
        "--new-engine",
        action="store_true",
        help="使用新的领域层引擎（影子模式）"
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
    submodule_parser.add_argument(
        "--new-engine",
        action="store_true",
        help="使用新的领域层引擎（影子模式）"
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
    """运行 auto-commit（支持影子模式）"""
    if getattr(args, "new_engine", False):
        from thera.workflow import WorkflowEngine
        repo_root = Path(args.repo)
        engine = WorkflowEngine(repo_root)
        
        print("[影子模式] 使用新引擎运行")
        
        if args.dry_run:
            status = engine.git_ops.get_status()
            if status.is_clean:
                print("无变更")
                return 0
            print(f"变更: {len(status.changes)} 个文件")
            for change in status.changes:
                print(f"  {change.change_type.name}: {change.path}")
            return 0
        
        result = engine.commit_and_push("[sync] auto commit from workflow")
        if result.success:
            print(f"✓ 推送成功: {result.commit_sha}")
            return 0
        else:
            print(f"✗ 失败: {result.message}")
            if result.error:
                print(f"  错误: {result.error}")
            return 1
    
    return auto_commit.main(args)


def run_doc_check(args):
    """运行 doc-check（支持影子模式）"""
    if getattr(args, "new_engine", False):
        from thera.workflow import WorkflowEngine
        repo_root = Path(args.repo)
        engine = WorkflowEngine(repo_root)
        
        config_path = getattr(args, "config", "meta/profile/submodules.yaml")
        print("[影子模式] 使用新引擎运行")
        
        result = engine.doc_check(Path(config_path))
        if result.is_consistent:
            print(f"✓ 一致性检查通过: {result.message}")
            return 0
        else:
            print(f"✗ 一致性检查失败: {result.message}")
            if result.missing_paths:
                print(f"  缺失路径: {', '.join(result.missing_paths)}")
            return 1
    
    return doc_check.main(args)


def run_submodule_sync(args):
    """运行 submodule-sync（支持影子模式）"""
    if getattr(args, "new_engine", False):
        from thera.workflow import WorkflowEngine
        repo_root = Path(args.repo)
        engine = WorkflowEngine(repo_root)
        
        print("[影子模式] 使用新引擎运行")
        
        if args.check:
            submodules = engine.git_ops.get_submodule_status()
            if not submodules:
                print("无子模块")
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
            print(f"✓ 同步完成: {result.message}")
            return 0
        else:
            print(f"✗ 同步失败: {result.message}")
            if result.error:
                print(f"  错误: {result.error}")
            return 1
    
    return submodule_sync.main(args)


if __name__ == "__main__":
    sys.exit(main())

"""
Thera CLI - 统一入口

Usage:
    thera auto-commit [--dry-run]
    thera doc-check [--repo PATH]
    thera submodule-sync [--check] [--sync PATHS] [--sync-all]
    thera --help
"""

import argparse
import sys

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
    
    doc_check_parser = subparsers.add_parser(
        "doc-check",
        help="检查文档一致性"
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
        return auto_commit.main(args)
    elif args.command == "doc-check":
        return doc_check.main(args)
    elif args.command == "submodule-sync":
        return submodule_sync.main(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

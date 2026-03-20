#!/usr/bin/env python3
"""
子模块同步脚本

检测子模块远程更新，生成变更摘要，支持选择性同步。
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_git(args: list[str], repo_root, capture: bool = True) -> str | bool:
    """运行 git 命令"""
    cmd = ["git", "-C", str(repo_root)] + args
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if capture:
        return result.stdout if result.stdout else ""
    else:
        return result.returncode == 0


def get_submodule_status(repo_root):
    """获取子模块状态"""
    output = run_git(["submodule", "status"], repo_root, True)  # type: ignore
    if not output:
        return []
    submodules = []
    for line in output.strip().split("\n"):  # type: ignore
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            status = parts[0]
            path = parts[1]
            has_update = status.startswith("+")
            submodules.append({
                "path": path,
                "local": status.lstrip("+")[:7],
                "has_update": has_update
            })
    return submodules


def sync_submodule(path, repo_root, verbose=False):
    """同步指定子模块"""
    print(f"同步 {path}...")
    success = run_git(["submodule", "update", "--remote", "--merge", path], repo_root, capture=False)
    if success:
        print(f"[OK] {path} 同步成功")
    else:
        print(f"[FAIL] {path} 同步失败")
    return success


def main(args=None):
    if args is None:
        parser = argparse.ArgumentParser(description="子模块同步工具")
        parser.add_argument("--check", action="store_true", help="检测远程更新")
        parser.add_argument("--sync", metavar="PATHS", help="同步指定子模块（逗号分隔）")
        parser.add_argument("--sync-all", action="store_true", help="同步所有子模块")
        parser.add_argument("--repo", default=".", help="仓库根目录")
        args = parser.parse_args()
    repo_root = Path(args.repo).resolve()
    
    if args.check:
        print("检测子模块更新...")
        submodules = get_submodule_status(repo_root)
        has_updates = any(s["has_update"] for s in submodules)
        
        if has_updates:
            print("\n检测到以下子模块有更新：")
            for s in submodules:
                if s["has_update"]:
                    print(f"  [UP] {s['path']} ({s['local']})")
        else:
            print("[OK] 所有子模块已是最新")
        return 0 if not has_updates else 1
    
    elif args.sync:
        paths = [p.strip() for p in args.sync.split(",")]
        for path in paths:
            sync_submodule(path, repo_root)
    
    elif args.sync_all:
        print("同步所有子模块...")
        run_git(["submodule", "update", "--remote", "--merge"], repo_root)
        print("[OK] 所有子模块同步完成")
    
    else:
        parser = argparse.ArgumentParser(description="子模块同步工具")
        parser.add_argument("--check", action="store_true", help="检测远程更新")
        parser.add_argument("--sync", metavar="PATHS", help="同步指定子模块（逗号分隔）")
        parser.add_argument("--sync-all", action="store_true", help="同步所有子模块")
        parser.add_argument("--repo", default=".", help="仓库根目录")
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

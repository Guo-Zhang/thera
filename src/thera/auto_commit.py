#!/usr/bin/env python3
"""
自动提交推送脚本

检测变更，交互确认后按序提交推送，并追加日志。
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_git(args, repo_root, capture=True):
    """运行 git 命令"""
    cmd = ["git", "-C", str(repo_root)] + args
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if capture:
        return result.stdout, result.stderr, result.returncode
    return None, None, result.returncode


def get_change_type(file_path):
    """根据文件路径识别变更类型"""
    if file_path.startswith("docs/"):
        return "docs"
    elif file_path.startswith("src/"):
        return "code"
    elif file_path in [".gitmodules", ".gitignore"]:
        return "config"
    elif file_path.startswith("meta/"):
        return "meta"
    else:
        return "root"


def get_repo_status(repo_root):
    """获取仓库变更状态"""
    stdout, _, _ = run_git(["status", "--porcelain"], repo_root)
    if not stdout:
        return []
    
    changes = []
    for line in stdout.strip().split("\n"):
        if not line:
            continue
        status = line[:2].strip()
        file_path = line[3:].strip()
        if file_path:
            changes.append({
                "status": status,
                "path": file_path,
                "type": get_change_type(file_path)
            })
    return changes


def get_submodule_status(repo_root):
    """获取子模块变更状态"""
    stdout, _, _ = run_git(["submodule", "status"], repo_root)
    if not stdout:
        return []
    
    submodules = []
    for line in stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            submodules.append(parts[1])
    return submodules


def format_changes(changes):
    """格式化变更列表为摘要"""
    if not changes:
        return "No changes"
    
    by_type = {}
    for change in changes:
        t = change["type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(change["path"])
    
    parts = []
    for t in sorted(by_type.keys()):
        files = by_type[t]
        if len(files) <= 3:
            parts.append(f"[{t}] {', '.join(files)}")
        else:
            parts.append(f"[{t}] {files[0]} (+{len(files)-1} more)")
    return ", ".join(parts)


def detect_all_changes(repo_root):
    """检测所有变更（子模块 + 主仓库）"""
    all_changes = {}
    
    submodules = get_submodule_status(repo_root)
    for submodule_path in submodules:
        submodule_full = repo_root / submodule_path
        changes = get_repo_status(submodule_full)
        if changes:
            all_changes[submodule_path] = changes
    
    main_changes = get_repo_status(repo_root)
    if main_changes:
        all_changes["."] = main_changes
    
    return all_changes


def display_changes(all_changes):
    """显示变更摘要"""
    if not all_changes:
        print("[OK] No changes detected")
        return False
    
    print("\nDetected changes:")
    print("-" * 50)
    
    for path in sorted(all_changes.keys()):
        changes = all_changes[path]
        label = "主仓库" if path == "." else path
        print(f"\n[{label}]")
        print(f"  {format_changes(changes)}")
    
    print("\n" + "-" * 50)
    return True


def confirm_commit(all_changes):
    """确认提交"""
    print("\nCommit and push these changes? [y/N/q]: ", end="")
    response = input().strip().lower()
    
    if response == "q":
        print("Aborted.")
        return False
    elif response == "y":
        return True
    else:
        print("No changes committed.")
        return False


def generate_commit_message(changes):
    """生成提交消息"""
    by_type = {}
    for change in changes:
        t = change["type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(change["path"])
    
    parts = []
    for t in sorted(by_type.keys()):
        files = by_type[t]
        parts.append(f"[{t}] {', '.join(files[:5])}")
        if len(files) > 5:
            parts[-1] += f" (+{len(files)-5} more)"
    
    return ", ".join(parts)


def commit_and_push(repo_root, path, changes, is_main=False):
    """提交并推送"""
    if path == ".":
        repo_label = "主仓库"
        log_label = "main"
    else:
        repo_label = path
        log_label = path
    
    print(f"\n>>> 处理 {repo_label}...")
    
    stdout, stderr, code = run_git(["add", "-A"], repo_root)
    if code != 0:
        print(f"[FAIL] git add failed: {stderr}")
        return False, log_label, []
    
    message = generate_commit_message(changes)
    if is_main:
        message = f"[sync] {message}"
    
    stdout, stderr, code = run_git(["commit", "-m", message], repo_root)
    if code != 0:
        if stderr and "nothing to commit" in stderr:
            print(f"[SKIP] {repo_label} - nothing to commit")
            return True, log_label, []
        print(f"[FAIL] git commit failed: {stderr}")
        return False, log_label, []
    
    print(f"  commit: {message[:60]}...")
    
    stdout, stderr, code = run_git(["push"], repo_root)
    if code != 0:
        print(f"[FAIL] git push failed: {stderr}")
        return False, log_label, []
    
    print(f"[OK] {repo_label} pushed")
    return True, log_label, changes


def append_journal(repo_root, results):
    """追加日志到 meta/journal/YYYY-MM-DD.md"""
    today = datetime.now().strftime("%Y-%m-%d")
    journal_path = repo_root / "meta" / "journal" / f"{today}.md"
    
    now = datetime.now().strftime("%H:%M")
    
    lines = []
    for success, repo, changes in results:
        if not success:
            status = "FAIL"
        elif not changes:
            status = "SKIP"
        else:
            status = "OK"
        
        by_type = {}
        for c in changes:
            t = c["type"]
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(c["path"])
        
        types_str = ", ".join(f"[{t}] {', '.join(files)}" for t, files in sorted(by_type.items()))
        
        repo_label = "main" if repo == "main" else repo
        lines.append(f"- {now} {status} {repo_label}: {types_str}")
    
    if lines:
        with open(journal_path, "a") as f:
            f.write("\n" + "\n".join(lines))
        print(f"\n[JOURNAL] Updated {journal_path}")


def main(args=None):
    if args is None:
        parser = argparse.ArgumentParser(description="自动提交推送工具")
        parser.add_argument("--repo", default=".", help="仓库根目录")
        parser.add_argument("--dry-run", action="store_true", help="仅显示变更，不提交")
        args = parser.parse_args()
    
    repo_root = Path(args.repo).resolve()
    
    print(f"Scanning repository: {repo_root}")
    all_changes = detect_all_changes(repo_root)
    
    if not display_changes(all_changes):
        return 0
    
    if args.dry_run:
        print("\nDry run - no changes made.")
        return 0
    
    if not confirm_commit(all_changes):
        return 0
    
    results = []
    
    submodule_paths = sorted([p for p in all_changes.keys() if p != "."])
    for submodule_path in submodule_paths:
        success, repo, changes = commit_and_push(
            repo_root / submodule_path,
            submodule_path,
            all_changes[submodule_path]
        )
        results.append((success, repo, changes))
    
    if "." in all_changes:
        success, repo, changes = commit_and_push(
            repo_root,
            ".",
            all_changes["."],
            is_main=True
        )
        results.append((success, repo, changes))
    
    append_journal(repo_root, results)
    
    failed = [r for r in results if not r[0]]
    if failed:
        print(f"\n[WARNING] {len(failed)} operation(s) failed")
        return 1
    
    print("\n[ALL DONE] All changes committed and pushed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

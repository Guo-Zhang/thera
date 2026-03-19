#!/usr/bin/env python3
"""
文档一致性检查脚本

从 YAML 事实源读取子模块配置，检查与 .gitmodules 的一致性。
"""

import argparse
import re
import sys
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def load_yaml_registry(config_path, repo_root):
    """从 YAML 事实源加载子模块注册表"""
    yaml_path = repo_root / config_path
    if not yaml_path.exists():
        return None
    
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    return data.get("submodules", []) if data else []


def check_gitmodules_vs_yaml(repo_root, config_path):
    """检查 .gitmodules 与 YAML 事实源的一致性"""
    gitmodules_path = repo_root / ".gitmodules"
    if not gitmodules_path.exists():
        return False, ".gitmodules 不存在"
    
    with open(gitmodules_path) as f:
        git_content = f.read()
    
    git_modules = {}
    current_name = None
    for line in git_content.split("\n"):
        name_match = re.match(r'\[submodule\s+"([^"]+)"\]', line)
        if name_match:
            current_name = name_match.group(1)
        path_match = re.match(r'\s*path\s*=\s*(.+)', line)
        if current_name and path_match:
            git_modules[current_name] = path_match.group(1).strip()
            current_name = None
    
    yaml_modules = load_yaml_registry(config_path, repo_root)
    if yaml_modules is None:
        return False, "YAML 事实源不存在"
    
    yaml_paths = {m["name"]: m["path"] for m in yaml_modules}
    
    errors = []
    
    git_names = set(git_modules.keys())
    yaml_names = set(yaml_paths.keys())
    
    missing_in_yaml = git_names - yaml_names
    if missing_in_yaml:
        errors.append(f"YAML 缺少: {', '.join(missing_in_yaml)}")
    
    missing_in_git = yaml_names - git_names
    if missing_in_git:
        errors.append(f".gitmodules 缺少: {', '.join(missing_in_git)}")
    
    path_mismatch = []
    for name in git_names & yaml_names:
        if git_modules[name] != yaml_paths[name]:
            path_mismatch.append(f"{name}: {git_modules[name]} vs {yaml_paths[name]}")
    if path_mismatch:
        errors.append(f"路径不一致: {', '.join(path_mismatch)}")
    
    all_exist = len(errors) == 0
    details = f"{len(yaml_paths)} 个子模块" if all_exist else "; ".join(errors)
    
    return all_exist, details


def check_yaml_paths(repo_root, config_path):
    """检查 YAML 中声明的路径是否存在"""
    yaml_modules = load_yaml_registry(config_path, repo_root)
    if yaml_modules is None:
        return False, "YAML 事实源不存在"
    
    missing = []
    for m in yaml_modules:
        path = repo_root / m["path"]
        if not path.exists():
            missing.append(m["path"])
    
    all_exist = len(missing) == 0
    details = f"{len(yaml_modules)} 个路径" if all_exist else f"缺失: {', '.join(missing)}"
    return all_exist, details


def main():
    parser = argparse.ArgumentParser(description="文档一致性检查")
    parser.add_argument("--config", default="meta/profile/submodules.yaml", help="YAML 配置文件路径")
    parser.add_argument("--repo", default=".", help="仓库根目录")
    args = parser.parse_args()
    
    repo_root = Path(args.repo).resolve()
    config_path = args.config
    
    print("=" * 60)
    print("文档一致性检查")
    print("=" * 60)
    print(f"仓库: {repo_root}")
    print(f"配置: {config_path}")
    print()
    
    checks = [
        ("YAML vs .gitmodules", lambda: check_gitmodules_vs_yaml(repo_root, config_path)),
        ("YAML 路径存在性", lambda: check_yaml_paths(repo_root, config_path)),
    ]
    
    results = []
    for name, check_func in checks:
        status, details = check_func()
        symbol = "[OK]" if status else "[WARN]"
        results.append((name, status, details))
        print(f"{symbol} {name:25s} {details}")
    
    print()
    print("=" * 60)
    all_pass = all(r[1] for r in results)
    if all_pass:
        print("[OK] 所有检查通过")
    else:
        print("[WARN] 存在不一致，请检查")
    print("=" * 60)
    
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())

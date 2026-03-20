"""pytest 配置和共享 fixtures"""

import os
import subprocess
import pytest
from pathlib import Path


@pytest.fixture
def git_repo(tmp_path):
    """创建一个临时 git 仓库用于测试"""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    
    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path, capture_output=True
    )
    
    (repo_path / "README.md").write_text("# Test\n")
    subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path, capture_output=True
    )
    
    return repo_path


@pytest.fixture
def git_repo_with_submodule(tmp_path):
    """创建一个有子模块的 git 仓库用于测试"""
    main_repo = tmp_path / "main_repo"
    sub_repo = tmp_path / "sub_repo"
    
    main_repo.mkdir()
    sub_repo.mkdir()
    
    subprocess.run(["git", "init"], cwd=sub_repo, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=sub_repo, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=sub_repo, capture_output=True
    )
    (sub_repo / "submodule_file.txt").write_text("submodule content")
    subprocess.run(["git", "add", "."], cwd=sub_repo, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Submodule initial"],
        cwd=sub_repo, capture_output=True
    )
    
    subprocess.run(["git", "init"], cwd=main_repo, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=main_repo, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=main_repo, capture_output=True
    )
    (main_repo / "main_file.txt").write_text("main content")
    subprocess.run(["git", "add", "."], cwd=main_repo, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Main initial"],
        cwd=main_repo, capture_output=True
    )
    
    subprocess.run(
        ["git", "submodule", "add", str(sub_repo), "docs/archive"],
        cwd=main_repo, capture_output=True
    )
    
    return main_repo

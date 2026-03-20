"""集成测试：测试 CLI 入口点"""

import subprocess
import sys
from pathlib import Path


class TestCliEntryPoints:
    """测试 CLI 入口点"""

    def test_auto_commit_help(self, git_repo):
        """测试 auto_commit --help"""
        result = subprocess.run(
            [sys.executable, "-m", "thera.auto_commit", "--help"],
            capture_output=True,
            text=True,
            cwd=str(git_repo),
        )
        assert result.returncode == 0
        assert "自动提交推送" in result.stdout or "auto-commit" in result.stdout.lower()

    def test_doc_check_help(self, git_repo):
        """测试 doc_check --help"""
        result = subprocess.run(
            [sys.executable, "-m", "thera.doc_check", "--help"],
            capture_output=True,
            text=True,
            cwd=str(git_repo),
        )
        assert result.returncode == 0
        assert "文档一致性检查" in result.stdout or "doc-check" in result.stdout.lower()

    def test_submodule_sync_help(self, git_repo):
        """测试 submodule_sync --help"""
        result = subprocess.run(
            [sys.executable, "-m", "thera.submodule_sync", "--help"],
            capture_output=True,
            text=True,
            cwd=str(git_repo),
        )
        assert result.returncode == 0
        assert "子模块同步" in result.stdout or "submodule-sync" in result.stdout.lower()

    def test_auto_commit_dry_run_no_changes(self, git_repo):
        """测试 auto_commit --dry-run 无变更"""
        result = subprocess.run(
            [sys.executable, "-m", "thera.auto_commit", "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(git_repo),
            input="n\n",  # 模拟用户输入 n
        )
        assert result.returncode == 0
        assert "No changes" in result.stdout or "无可用变更" in result.stdout

    def test_doc_check_no_yaml(self, git_repo):
        """测试 doc-check 无 YAML 文件"""
        result = subprocess.run(
            [sys.executable, "-m", "thera.doc_check"],
            capture_output=True,
            text=True,
            cwd=str(git_repo),
        )
        # 应该返回非零退出码因为 YAML 不存在
        assert result.returncode != 0 or "不存在" in result.stdout

    def test_submodule_sync_check_no_submodules(self, git_repo):
        """测试 submodule-sync --check 无子模块"""
        result = subprocess.run(
            [sys.executable, "-m", "thera.submodule_sync", "--check"],
            capture_output=True,
            text=True,
            cwd=str(git_repo),
        )
        # 无子模块时应该返回 0
        assert result.returncode == 0

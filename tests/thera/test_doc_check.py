"""测试文档一致性检查功能"""

import argparse
import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from thera import doc_check


class TestLoadYamlRegistry:
    """测试 load_yaml_registry 函数"""

    def test_yaml_exists(self, tmp_path):
        """测试 YAML 文件存在"""
        yaml_content = """
submodules:
  - name: "archive"
    path: "docs/archive"
"""
        yaml_path = tmp_path / "meta" / "profile" / "submodules.yaml"
        yaml_path.parent.mkdir(parents=True)
        yaml_path.write_text(yaml_content)
        
        result = doc_check.load_yaml_registry("meta/profile/submodules.yaml", tmp_path)
        assert result is not None
        assert len(result) == 1
        assert result[0]["name"] == "archive"

    def test_yaml_not_exists(self, tmp_path):
        """测试 YAML 文件不存在"""
        result = doc_check.load_yaml_registry("meta/profile/not_exist.yaml", tmp_path)
        assert result is None

    def test_yaml_empty(self, tmp_path):
        """测试 YAML 文件为空"""
        yaml_path = tmp_path / "meta" / "profile" / "empty.yaml"
        yaml_path.parent.mkdir(parents=True)
        yaml_path.write_text("")
        
        result = doc_check.load_yaml_registry("meta/profile/empty.yaml", tmp_path)
        assert result == []

    def test_yaml_no_submodules_key(self, tmp_path):
        """测试 YAML 无 submodules 键"""
        yaml_content = """
other_key: value
"""
        yaml_path = tmp_path / "test.yaml"
        yaml_path.write_text(yaml_content)
        
        result = doc_check.load_yaml_registry("test.yaml", tmp_path)
        assert result == []


class TestCheckGitmodulesVsYaml:
    """测试 check_gitmodules_vs_yaml 函数"""

    def test_gitmodules_not_exists(self, tmp_path):
        """测试 .gitmodules 不存在"""
        result = doc_check.check_gitmodules_vs_yaml(tmp_path, "test.yaml")
        assert result == (False, ".gitmodules 不存在")

    def test_yaml_not_exists(self, tmp_path, git_repo):
        """测试 YAML 不存在"""
        # 先创建 .gitmodules，这样能测试到 YAML 不存在的分支
        gitmodules_content = '''
[submodule "archive"]
\tpath = docs/archive
'''
        (git_repo / ".gitmodules").write_text(gitmodules_content)
        
        result = doc_check.check_gitmodules_vs_yaml(git_repo, "not_exist.yaml")
        assert result[0] is False
        assert "不存在" in result[1]

    def test_consistent(self, tmp_path, git_repo):
        """测试完全一致的情况"""
        gitmodules_content = '''
[submodule "archive"]
\tpath = docs/archive
\turl = https://github.com/quanttide/quanttide-archive-of-founder.git
'''
        (git_repo / ".gitmodules").write_text(gitmodules_content)
        
        yaml_content = """
submodules:
  - name: "archive"
    path: "docs/archive"
"""
        yaml_path = git_repo / "meta" / "profile" / "submodules.yaml"
        yaml_path.parent.mkdir(parents=True)
        yaml_path.write_text(yaml_content)
        
        result = doc_check.check_gitmodules_vs_yaml(git_repo, "meta/profile/submodules.yaml")
        assert result[0] is True
        assert "1 个子模块" in result[1]

    def test_missing_in_yaml(self, tmp_path, git_repo):
        """测试 YAML 缺少子模块"""
        gitmodules_content = '''
[submodule "archive"]
\tpath = docs/archive
[submodule "thera"]
\tpath = src/thera
'''
        (git_repo / ".gitmodules").write_text(gitmodules_content)
        
        yaml_content = """
submodules:
  - name: "archive"
    path: "docs/archive"
"""
        yaml_path = git_repo / "meta" / "profile" / "submodules.yaml"
        yaml_path.parent.mkdir(parents=True)
        yaml_path.write_text(yaml_content)
        
        result = doc_check.check_gitmodules_vs_yaml(git_repo, "meta/profile/submodules.yaml")
        assert result[0] is False
        assert "YAML 缺少: thera" in result[1]

    def test_missing_in_gitmodules(self, tmp_path, git_repo):
        """测试 .gitmodules 缺少子模块"""
        gitmodules_content = '''
[submodule "archive"]
\tpath = docs/archive
'''
        (git_repo / ".gitmodules").write_text(gitmodules_content)
        
        yaml_content = """
submodules:
  - name: "archive"
    path: "docs/archive"
  - name: "thera"
    path: "src/thera"
"""
        yaml_path = git_repo / "meta" / "profile" / "submodules.yaml"
        yaml_path.parent.mkdir(parents=True)
        yaml_path.write_text(yaml_content)
        
        result = doc_check.check_gitmodules_vs_yaml(git_repo, "meta/profile/submodules.yaml")
        assert result[0] is False
        assert ".gitmodules 缺少: thera" in result[1]

    def test_path_mismatch(self, tmp_path, git_repo):
        """测试路径不一致"""
        gitmodules_content = '''
[submodule "archive"]
\tpath = docs/archive
'''
        (git_repo / ".gitmodules").write_text(gitmodules_content)
        
        yaml_content = """
submodules:
  - name: "archive"
    path: "docs/old-archive"
"""
        yaml_path = git_repo / "meta" / "profile" / "submodules.yaml"
        yaml_path.parent.mkdir(parents=True)
        yaml_path.write_text(yaml_content)
        
        result = doc_check.check_gitmodules_vs_yaml(git_repo, "meta/profile/submodules.yaml")
        assert result[0] is False
        assert "路径不一致" in result[1]

    def test_multiple_errors(self, tmp_path, git_repo):
        """测试多个错误"""
        gitmodules_content = '''
[submodule "archive"]
\tpath = docs/archive
[submodule "thera"]
\tpath = src/thera
'''
        (git_repo / ".gitmodules").write_text(gitmodules_content)
        
        yaml_content = """
submodules:
  - name: "archive"
    path: "docs/old"
"""
        yaml_path = git_repo / "meta" / "profile" / "submodules.yaml"
        yaml_path.parent.mkdir(parents=True)
        yaml_path.write_text(yaml_content)
        
        result = doc_check.check_gitmodules_vs_yaml(git_repo, "meta/profile/submodules.yaml")
        assert result[0] is False


class TestCheckYamlPaths:
    """测试 check_yaml_paths 函数"""

    def test_yaml_not_exists(self, tmp_path):
        """测试 YAML 不存在"""
        result = doc_check.check_yaml_paths(tmp_path, "not_exist.yaml")
        assert result[0] is False
        assert "不存在" in result[1]

    def test_all_paths_exist(self, tmp_path, git_repo):
        """测试所有路径存在"""
        yaml_content = """
submodules:
  - name: "archive"
    path: "docs/archive"
  - name: "thera"
    path: "src/thera"
"""
        yaml_path = git_repo / "meta" / "profile" / "submodules.yaml"
        yaml_path.parent.mkdir(parents=True)
        yaml_path.write_text(yaml_content)
        
        (git_repo / "docs" / "archive").mkdir(parents=True)
        (git_repo / "src" / "thera").mkdir(parents=True)
        
        result = doc_check.check_yaml_paths(git_repo, "meta/profile/submodules.yaml")
        assert result[0] is True
        assert "2 个路径" in result[1]

    def test_missing_paths(self, tmp_path, git_repo):
        """测试路径缺失"""
        yaml_content = """
submodules:
  - name: "archive"
    path: "docs/archive"
  - name: "thera"
    path: "src/thera"
"""
        yaml_path = git_repo / "meta" / "profile" / "submodules.yaml"
        yaml_path.parent.mkdir(parents=True)
        yaml_path.write_text(yaml_content)
        
        (git_repo / "docs" / "archive").mkdir(parents=True)
        
        result = doc_check.check_yaml_paths(git_repo, "meta/profile/submodules.yaml")
        assert result[0] is False
        assert "缺失" in result[1]


class TestMain:
    """测试 main 函数"""

    def test_all_pass(self, tmp_path, git_repo):
        """测试所有检查通过"""
        gitmodules_content = '''
[submodule "archive"]
\tpath = docs/archive
'''
        (git_repo / ".gitmodules").write_text(gitmodules_content)
        
        yaml_content = """
submodules:
  - name: "archive"
    path: "docs/archive"
"""
        yaml_path = git_repo / "meta" / "profile" / "submodules.yaml"
        yaml_path.parent.mkdir(parents=True)
        yaml_path.write_text(yaml_content)
        
        (git_repo / "docs" / "archive").mkdir(parents=True)
        
        with patch("builtins.print"):
            args = argparse.Namespace(
                config="meta/profile/submodules.yaml",
                repo=str(git_repo)
            )
            result = doc_check.main(args)
            assert result == 0

    def test_has_warnings(self, tmp_path, git_repo):
        """测试存在警告"""
        gitmodules_content = '''
[submodule "archive"]
\tpath = docs/archive
'''
        (git_repo / ".gitmodules").write_text(gitmodules_content)
        
        yaml_content = """
submodules:
  - name: "archive"
    path: "docs/old"
"""
        yaml_path = git_repo / "meta" / "profile" / "submodules.yaml"
        yaml_path.parent.mkdir(parents=True)
        yaml_path.write_text(yaml_content)
        
        with patch("builtins.print"):
            args = argparse.Namespace(
                config="meta/profile/submodules.yaml",
                repo=str(git_repo)
            )
            result = doc_check.main(args)
            assert result == 1

    def test_argparse_default_args(self, tmp_path, git_repo):
        """测试 argparse 默认参数路径（覆盖 99-102 行）"""
        gitmodules_content = '''
[submodule "archive"]
\tpath = docs/archive
'''
        (git_repo / ".gitmodules").write_text(gitmodules_content)
        
        yaml_content = """
submodules:
  - name: "archive"
    path: "docs/archive"
"""
        yaml_path = git_repo / "meta" / "profile" / "submodules.yaml"
        yaml_path.parent.mkdir(parents=True)
        yaml_path.write_text(yaml_content)
        
        (git_repo / "docs" / "archive").mkdir(parents=True)
        
        with patch("builtins.print"):
            # Patch sys.argv to use git_repo as the repo path
            with patch("sys.argv", ["doc_check.py", "--repo", str(git_repo)]):
                result = doc_check.main()
                assert result == 0

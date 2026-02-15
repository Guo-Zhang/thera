"""
思考域单元测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from thera.__main__ import Thera
from thera.state.storage_state import StorageState
from thera.domain.think_domain import ThinkDomain


class TestThinkDomain:
    def test_domain_creation(self):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = ThinkDomain(app)
        assert domain.name == "think"
        assert domain.description == "思考域 - 头脑风暴、深度分析"

    def test_handle_input(self):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = ThinkDomain(app)
        result = domain.handle_input("今天天气真好")
        assert "[Think]" in result

    def test_on_activate(self):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = ThinkDomain(app)
        domain.on_activate()

    def test_on_deactivate(self):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = ThinkDomain(app)
        domain.on_deactivate()

    def test_auto_switch_to_write(self):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = ThinkDomain(app)
        result = domain.auto_switch("/write")
        assert result.value == "write"

    def test_auto_switch_to_knowl(self):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = ThinkDomain(app)
        result = domain.auto_switch("/knowl")
        assert result.value == "knowl"

    def test_auto_switch_no_match(self):
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = ThinkDomain(app)
        result = domain.auto_switch("今天天气真好")
        assert result is None


class TestThinkWorkflow:
    """想法碎片工作流测试"""

    def test_idea_classification_work(self):
        """测试工作类想法分类"""
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = ThinkDomain(app)

        work_ideas = [
            "完成项目报告",
            "准备明天会议",
            "回复客户邮件",
        ]

        for idea in work_ideas:
            result = domain.classify_idea(idea)
            assert result == "work", f"'{idea}' should be classified as work"

    def test_idea_classification_life(self):
        """测试生活类想法分类"""
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = ThinkDomain(app)

        life_ideas = [
            "去超市买菜",
            "健身锻炼",
            "看一部电影",
        ]

        for idea in life_ideas:
            result = domain.classify_idea(idea)
            assert result == "life", f"'{idea}' should be classified as life"

    def test_idea_classification_unknown(self):
        """测试未知分类"""
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = ThinkDomain(app)

        result = domain.classify_idea("asdfghjkl")
        assert result == "unknown"

    def test_save_idea_to_storage(self):
        """测试保存想法到存储"""
        app = Thera(storage_path=Path("/tmp/test_thera"))
        app.init()

        domain = ThinkDomain(app)
        domain.save_idea("测试想法", "work")

        ideas = app.storage.load_json("think", "ideas.json")
        assert ideas is not None
        assert len(ideas) > 0

    def test_think_tools_integration(self):
        """测试思考工具集成"""
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = ThinkDomain(app)

        tools = domain.get_tools()
        assert "brainstorm" in tools
        assert "analyze" in tools

    def test_auto_switch_work_idea(self):
        """测试工作类想法自动切换"""
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = ThinkDomain(app)

        result = domain.auto_switch("/think 工作项目启动")
        assert result is None or result.value == "think"

    def test_list_ideas(self):
        """测试列出想法"""
        app = Thera(storage_path=Path("/tmp/test_thera"))
        domain = ThinkDomain(app)

        result = domain._list_ideas()
        assert "No ideas" in result

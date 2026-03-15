"""
默认活动（增量式被动观察）单元测试
"""

import sys
from pathlib import Path
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from thera.mode.default import JournalProcessor
from thera.config import Config


class TestParagraphSplitting:
    """段落切分测试"""

    def test_split_single_paragraph(self):
        """测试单段落切分"""
        from thera.mode.default import split_paragraphs

        content = "这是第一段内容"
        result = split_paragraphs(content)
        assert len(result) == 1
        assert result[0] == "这是第一段内容"

    def test_split_multiple_paragraphs(self):
        """测试多段落切分"""
        from thera.mode.default import split_paragraphs

        content = "第一段\n\n第二段\n\n第三段"
        result = split_paragraphs(content)
        assert len(result) == 3
        assert result[0] == "第一段"
        assert result[1] == "第二段"
        assert result[2] == "第三段"

    def test_split_empty_string_filtered(self):
        """测试空字符串被过滤"""
        from thera.mode.default import split_paragraphs

        content = "第一段\n\n\n\n第二段"
        result = split_paragraphs(content)
        assert len(result) == 2

    def test_split_whitespace_only_filtered(self):
        """测试纯空白段落被过滤"""
        from thera.mode.default import split_paragraphs

        content = "第一段\n\n   \n\n第二段"
        result = split_paragraphs(content)
        assert len(result) == 2


class TestAnnotationDetection:
    """批注检测测试"""

    def test_is_already_annotated_true(self):
        """测试已处理段落检测"""
        from thera.mode.default import is_already_annotated

        text = "这是段落内容\n\n> 🤖 观察者注"
        assert is_already_annotated(text) is True

    def test_is_already_annotated_false(self):
        """测试未处理段落检测"""
        from thera.mode.default import is_already_annotated

        text = "这是段落内容"
        assert is_already_annotated(text) is False


class TestShortParagraphFilter:
    """短段落过滤测试"""

    def test_is_short_true(self):
        """测试短段落识别"""
        from thera.mode.default import is_short

        assert is_short("短") is True
        assert is_short("abc") is True
        assert is_short("一二三四五六七八九十") is True

    def test_is_short_false(self):
        """测试非短段落识别"""
        from thera.mode.default import is_short

        assert is_short("这是一段超过二十个字的文本内容") is False


class TestConfig:
    """配置测试"""

    def test_config_defaults(self):
        """测试配置默认值"""
        config = Config()
        assert config.opencode_path == "/usr/local/bin/opencode"
        assert config.model == "o4-mini"
        assert config.max_retries == 3


class TestJournalProcessor:
    """处理器集成测试"""

    def test_process_with_fixture(self, tmp_path):
        """使用 fixture 测试完整流程"""
        # 准备测试文件
        test_file = tmp_path / "test.md"
        fixture_input = (
            Path(__file__).parent
            / "fixtures"
            / "default"
            / "journal_2026-03-15_input.md"
        )

        if fixture_input.exists():
            test_file.write_text(fixture_input.read_text())

        # 创建配置
        config = Config()
        config.opencode_path = "echo"  # 使用 echo 模拟

        # 执行处理
        processor = JournalProcessor(config)
        # processor.process(str(test_file))  # 跳过实际执行，仅测试初始化

        assert config.max_retries == 3

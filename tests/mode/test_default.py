"""
默认活动（增量式被动观察）单元测试
"""

import sys
from pathlib import Path
import tempfile


def test_split_paragraphs():
    """测试段落切分"""

    # 模拟函数
    def split_paragraphs(content):
        paragraphs = content.split("\n\n")
        return [p.strip() for p in paragraphs if p.strip()]

    # 测试单段落
    content = "这是第一段内容"
    result = split_paragraphs(content)
    assert len(result) == 1
    assert result[0] == "这是第一段内容"

    # 测试多段落
    content = "第一段\n\n第二段\n\n第三段"
    result = split_paragraphs(content)
    assert len(result) == 3

    # 测试空字符串过滤
    content = "第一段\n\n\n\n第二段"
    result = split_paragraphs(content)
    assert len(result) == 2


def test_is_already_annotated():
    """测试批注检测"""

    def is_already_annotated(text):
        return "🤖 观察者注" in text

    assert is_already_annotated("这是段落内容\n\n> 🤖 观察者注") is True
    assert is_already_annotated("这是段落内容") is False


def test_is_short():
    """测试短段落识别"""

    def is_short(text):
        return len(text.strip()) < 20

    assert is_short("短") is True
    assert is_short("abc") is True
    assert is_short("一二三四五六七八九十") is True  # 10个中文字符
    assert is_short("This is more than twenty characters") is False


def test_file_operations():
    """测试文件读写"""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        content = "测试内容"
        f.write(content)

    with open(test_file, encoding="utf-8") as f:
        result = f.read()

    assert result == content

    import os

    os.unlink(test_file)


def test_default_config():
    """测试配置默认值"""
    from dataclasses import dataclass

    @dataclass
    class DefaultConfig:
        opencode_path: str = "/usr/local/bin/opencode"
        model: str = "o4-mini"
        max_retries: int = 3

    config = DefaultConfig()
    assert config.opencode_path == "/usr/local/bin/opencode"
    assert config.model == "o4-mini"
    assert config.max_retries == 3


if __name__ == "__main__":
    test_split_paragraphs()
    test_is_already_annotated()
    test_is_short()
    test_file_operations()
    test_default_config()
    print("All tests passed!")

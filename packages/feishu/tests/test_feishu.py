"""
quanttide-feishu tests
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest


class TestConverter:
    """测试转换器"""

    def test_apply_style_bold(self):
        """测试加粗样式"""
        from quanttide_feishu.converter import apply_style

        result = apply_style("text", {"bold": True})
        assert result == "**text**"

    def test_apply_style_italic(self):
        """测试斜体样式"""
        from quanttide_feishu.converter import apply_style

        result = apply_style("text", {"italic": True})
        assert result == "*text*"

    def test_apply_style_link(self):
        """测试链接样式"""
        from quanttide_feishu.converter import apply_style

        result = apply_style("text", {"link": "https://example.com"})
        assert result == "[text](https://example.com)"

    def test_get_safe_filename(self):
        """测试安全文件名"""
        from quanttide_feishu.converter import get_safe_filename

        assert get_safe_filename("Test 文档") == "Test 文档"
        assert get_safe_filename("test/doc") == "test doc"
        assert get_safe_filename("") == "unnamed"

    def test_block_type_to_markdown_text(self):
        """测试文本块转换"""
        from quanttide_feishu.converter import block_type_to_markdown

        block = {
            "block_type": 2,
            "text": {
                "elements": [{"text_run": {"content": "Hello World", "style": None}}]
            },
        }
        result = block_type_to_markdown(block)
        assert "Hello World" in result

    def test_block_type_to_markdown_heading(self):
        """测试标题块转换"""
        from quanttide_feishu.converter import block_type_to_markdown

        block = {
            "block_type": 3,
            "text": {"elements": [{"text_run": {"content": "Title", "style": None}}]},
        }
        result = block_type_to_markdown(block)
        assert result.startswith("# Title")

    def test_block_type_to_markdown_bullet(self):
        """测试无序列表块转换"""
        from quanttide_feishu.converter import block_type_to_markdown

        block = {
            "block_type": 12,
            "text": {"elements": [{"text_run": {"content": "Item", "style": None}}]},
        }
        result = block_type_to_markdown(block)
        assert result.startswith("- Item")


class TestClient:
    """测试客户端"""

    def test_create_lark_client_missing_env(self):
        """测试缺少环境变量"""
        from quanttide_feishu.client import create_lark_client

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError):
                create_lark_client()

    def test_create_lark_client_with_env(self):
        """测试带环境变量"""
        from quanttide_feishu.client import create_lark_client

        with patch.dict(
            "os.environ",
            {"FEISHU_APP_ID": "test_id", "FEISHU_APP_SECRET": "test_secret"},
        ):
            with patch("quanttide_feishu.client.Client") as mock_client:
                mock_client.builder.return_value.app_id.return_value.app_secret.return_value.log_level.return_value.build.return_value = "client"
                result = create_lark_client()
                assert result == "client"

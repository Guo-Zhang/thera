"""
测试 thera.llm.DeepSeekClient
"""
import unittest
from unittest.mock import patch

from src.thera.llm import DeepSeekClient


class TestDeepSeekClient(unittest.TestCase):

    @patch("openai.ChatCompletion.create")
    def test_generate_returns_text(self, mock_create):
        # 模拟一个常见的 chat-style 返回结构
        mock_create.return_value = {
            "choices": [
                {"message": {"content": "这是生成的文本。"}}
            ]
        }

        client = DeepSeekClient(api_key="test-key", model="test-model")
        out = client.generate("你好")
        self.assertEqual(out, "这是生成的文本。")
        mock_create.assert_called_once()

    @patch("openai.ChatCompletion.create")
    def test_generate_uses_text_field_if_no_message(self, mock_create):
        mock_create.return_value = {"choices": [{"text": "fallback 文本"}]}
        client = DeepSeekClient(api_key="k", model="m")
        out = client.generate("hi")
        self.assertEqual(out, "fallback 文本")

    def test_init_raises_without_api_key(self):
        # Ensure missing API key raises
        with self.assertRaises(RuntimeError):
            DeepSeekClient(api_key=None, model="m")

    def test_generate_invalid_prompt(self):
        client = DeepSeekClient(api_key="k", model="m")
        with self.assertRaises(ValueError):
            client.generate("")


if __name__ == "__main__":
    unittest.main()

"""
大模型调用模块

thera.llm
=================

封装 DeepSeek（或兼容 OpenAI 接口的模型）的小型客户端。

提供:
- DeepSeekClient: 轻量封装，使用 openai 包调用聊天/Completion 接口。

设计目标：最小、可测、在没有外部依赖（除 openai）时可运行的封装。
"""

import os
from typing import Optional

try:
	import openai
except Exception:  # pragma: no cover - fallback when openai is not installed
	# Provide a tiny shim so tests can patch openai.ChatCompletion.create
	class _OpenAIShim:
		class ChatCompletion:
			@staticmethod
			def create(*_args, **_kwargs):
				raise RuntimeError("openai package is not installed")

	openai = _OpenAIShim()


class DeepSeekClient:
	"""A thin wrapper around an OpenAI-compatible chat/completion model.

	It reads the model name from the `SILICONFLOW_MODEL` env var by default and
	the API key from `OPENAI_API_KEY`. A custom `api_key` or `base_url` can be
	passed to override environment settings (useful for testing).

	Usage:
		client = DeepSeekClient()
		text = client.generate("请帮我写一段关于深度学习的简介。")
	"""

	def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None, base_url: Optional[str] = None):
		self.model = model or os.getenv("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V3.1-Terminus")
		self.api_key = api_key or os.getenv("OPENAI_API_KEY")

		if not self.api_key:
			# Fail fast — caller should provide credentials
			raise RuntimeError("OPENAI_API_KEY is not set; provide api_key or set environment variable")

		openai.api_key = self.api_key

		# Optionally override API base (useful if using a proxy or non-openai host)
		if base_url:
			openai.api_base = base_url

	def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.0) -> str:
		"""Generate a completion from the model.

		Args:
			prompt: the user prompt / input text.
			max_tokens: maximum tokens to generate.
			temperature: sampling temperature.

		Returns:
			The generated text (stripped).

		Raises:
			ValueError: if prompt is empty or not a string.
			RuntimeError: if model returns no content.
		"""
		if not prompt or not isinstance(prompt, str):
			raise ValueError("prompt must be a non-empty string")

		# We call the chat-style API for broad compatibility. Many providers
		# that are OpenAI-compatible accept the same parameters.
		resp = openai.ChatCompletion.create(
			model=self.model,
			messages=[{"role": "user", "content": prompt}],
			max_tokens=max_tokens,
			temperature=temperature,
		)

		# Response formats vary slightly between providers. Try to extract
		# the textual content in a robust way.
		choices = resp.get("choices") or []
		if not choices:
			raise RuntimeError("model returned no choices")

		first = choices[0]
		# Newer chat responses put the text under message.content
		text = ""
		if isinstance(first.get("message"), dict):
			text = first.get("message", {}).get("content", "")
		# Some providers (or older responses) may use `text`
		if not text:
			text = first.get("text", "")

		return (text or "").strip()


"""
LLM 基础设施模块
"""

import json
import re
from typing import Any

from openai import OpenAI

from thera.config import settings


def create_client() -> OpenAI:
    """创建 LLM 客户端"""
    return OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)


def chat(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.7,
    stream: bool = False,
):
    """通用聊天接口"""
    client = create_client()
    return client.chat.completions.create(
        model=model or settings.llm_model,
        messages=messages,
        temperature=temperature,
        stream=stream,
    )


def chat_str(
    prompt: str,
    system_prompt: str = "",
    model: str | None = None,
    temperature: float = 0.7,
) -> str:
    """聊天并返回字符串"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = chat(messages, model, temperature)
    return response.choices[0].message.content or ""


def stream(prompt: str, system_prompt: str = ""):
    """流式输出"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = chat(messages, stream=True)
    for chunk in response:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
            yield delta.reasoning_content


def _parse_json(response: str) -> dict[str, Any]:
    """解析 JSON 响应"""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    return {}


def json_request(prompt: str, system_prompt: str = "") -> dict[str, Any]:
    """请求 JSON 格式响应"""
    result = chat_str(prompt, system_prompt)
    return _parse_json(result)


def get_embeddings(texts: list[str], batch_size: int = 10):
    """获取文本嵌入向量"""
    client = create_client()

    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(
            model=settings.llm_embedding_model, input=batch
        )
        all_embeddings.extend([d.embedding for d in response.data])

    return all_embeddings


def get_embedding(text: str) -> list[float]:
    """获取单个文本的嵌入向量"""
    return get_embeddings([text])[0]


if __name__ == "__main__":
    client = create_client()
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": "推理模型会给市场带来哪些新的机会"}],
        stream=True,
    )

    for chunk in response:
        if not chunk.choices:
            continue
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
        if chunk.choices[0].delta.reasoning_content:
            print(chunk.choices[0].delta.reasoning_content, end="", flush=True)

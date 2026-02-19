"""
LLM 调用模块
"""

import json
import re
from typing import Any, Iterator

from openai import OpenAI


def create_client(api_key: str = None, base_url: str = None) -> OpenAI:
    """创建 LLM 客户端"""
    from .config import get_settings

    settings = get_settings()
    return OpenAI(
        api_key=api_key or settings.llm_api_key,
        base_url=base_url or settings.llm_base_url,
    )


def chat(
    client: OpenAI,
    messages: list[dict[str, str]],
    model: str = None,
    temperature: float = 0.7,
    stream: bool = False,
):
    """通用聊天接口"""
    from .config import get_settings

    settings = get_settings()
    return client.chat.completions.create(
        model=model or settings.llm_model,
        messages=messages,
        temperature=temperature,
        stream=stream,
    )


def chat_str(
    prompt: str,
    system_prompt: str = "",
    model: str = None,
    temperature: float = 0.7,
    api_key: str = None,
    base_url: str = None,
) -> str:
    """聊天并返回字符串"""
    client = create_client(api_key, base_url)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = chat(client, messages, model, temperature)
    return response.choices[0].message.content or ""


def stream(
    prompt: str,
    system_prompt: str = "",
    model: str = None,
    temperature: float = 0.7,
    api_key: str = None,
    base_url: str = None,
) -> Iterator[str]:
    """流式输出"""
    client = create_client(api_key, base_url)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = chat(client, messages, model, temperature, stream=True)
    for chunk in response:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
            yield delta.reasoning_content


def json_request(
    prompt: str,
    system_prompt: str = "",
    model: str = None,
    temperature: float = 0.7,
    api_key: str = None,
    base_url: str = None,
) -> dict[str, Any]:
    """请求 JSON 格式响应"""
    result = chat_str(prompt, system_prompt, model, temperature, api_key, base_url)

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", result, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    return {}

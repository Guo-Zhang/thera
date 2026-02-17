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


def extract_triplets(
    items: list[dict[str, str]],
    format_fn: callable,
    max_items: int = 8,
    max_content: int = 800,
) -> str:
    """通用三元组抽取"""
    combined = "\n\n".join(
        [format_fn(item)[:max_content] for item in items[:max_items]]
    )
    prompt = f"""从以下文本中提取知识图谱三元组。
要求：
1. 提取实体和它们之间的关系
2. 关系用动词或介词短语表示
3. 只提取核心知识，忽略描述性内容

内容：
{combined}

请以以下TTL格式输出（只输出TTL，不要其他内容）：
@prefix kb: <http://example.org/knowledge/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

kb:实体1 rdfs:label "实体1" .
kb:实体2 rdfs:label "实体2" .
kb:实体1 kb:关系 kb:实体2 .
"""
    return chat_str(prompt, temperature=0.3)


def summarize_content(
    items: list[dict[str, Any]],
    format_fn: callable,
    max_items: int = 10,
    max_content: int = 500,
    max_length: int = 200,
) -> str:
    """通用内容总结"""
    sample = items[:max_items]
    combined = "\n\n".join([format_fn(item)[:max_content] for item in sample])
    prompt = f"""请为以下内容生成一个简洁的介绍（{max_length}字以内）。

内容：
{combined}

请直接输出介绍内容，不要其他格式。
"""
    return chat_str(prompt, temperature=0.3)


def evaluate_content_quality(
    items: list[dict[str, Any]],
    format_fn: callable,
    criteria: dict[str, str],
    max_items: int = 8,
    max_content: int = 600,
) -> dict[str, Any]:
    """通用内容质量评估"""
    sample = items[:max_items]
    combined = "\n\n".join([format_fn(item)[:max_content] for item in sample])

    criteria_str = "\n".join([f'"{k}": {v}' for k, v in criteria.items()])

    prompt = f"""请评估以下内容的质量。

内容：
{combined}

请从以下维度评估并输出JSON格式结果：
{{
    {criteria_str}
}}

只输出JSON，不要其他内容。
"""
    result = json_request(prompt)
    return result or {"error": "评估失败"}


def evaluate_ttl_quality(
    ttl_content: str,
    item_titles: list[str],
    criteria: dict[str, str],
    context: str = "",
) -> dict[str, Any]:
    """通用 TTL 质量评估"""
    criteria_str = "\n".join([f'"{k}": {v}' for k, v in criteria.items()])

    prompt = f"""{context}
知识图谱内容：
{ttl_content}

相关标题：{item_titles}

请从以下维度评估并输出JSON格式结果：
{{
    {criteria_str}
}}

只输出JSON，不要其他内容。
"""
    result = json_request(prompt)
    return result or {"error": "评估失败"}


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

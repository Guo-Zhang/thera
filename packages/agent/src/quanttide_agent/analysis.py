"""
分析模块 - LLM 驱动的分析功能
"""

import json
import re
from typing import Any, Callable

from quanttide_agent.llm import chat_str, json_request


def extract_keywords(texts: list[str], top_n: int = 15) -> list[str]:
    """提取关键词"""
    from collections import Counter

    all_text = " ".join(texts)
    words = re.findall(r"[\u4e00-\u9fa5]{2,4}", all_text)
    counter = Counter(words)
    return [w for w, _ in counter.most_common(top_n)]


def extract_triplets(
    items: list[dict[str, str]],
    format_fn: Callable[[dict], str],
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
    format_fn: Callable[[dict], str],
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
    format_fn: Callable[[dict], str],
    criteria: dict[str, str],
    max_items: int = 8,
    max_content: int = 600,
) -> dict[str, Any]:
    """通用内容质量评估"""
    sample = items[:max_items]
    combined = "\n\n".join([format_fn(item)[:max_content] for item in sample])

    criteria_lines = "\n".join([f"- {v}" for v in criteria.values()])

    prompt = f"""请评估以下内容的质量。

内容：
{combined}

请从以下维度评估并输出JSON格式结果：
{criteria_lines}
"""
    return json_request(prompt)


def evaluate_ttl_quality(
    ttl_content: str,
    item_titles: list[str],
    criteria: dict[str, str],
    context: str = "",
) -> dict[str, Any]:
    """通用 TTL 质量评估"""
    criteria_lines = "\n".join([f"- {v}" for v in criteria.values()])

    prompt = f"""{context}
知识图谱内容：
{ttl_content}

相关标题：{item_titles}

请从以下维度评估并输出JSON格式结果：
{criteria_lines}
"""
    return json_request(prompt)


def analyze_development_direction(
    items: list[dict[str, Any]],
    format_fn: Callable[[dict], str],
    clusters: list[dict[str, Any]],
    max_clusters: int = 5,
) -> dict[str, Any]:
    """分析发展方向"""
    prompt = f"""请分析以下内容集合的发展方向和趋势。

内容总数: {len(items)}
分组数: {len(clusters)}

"""
    if clusters:
        prompt += "各分组概述:\n"
        for cluster in clusters[:max_clusters]:
            prompt += f"- 分组 {cluster['cluster_id']}: {cluster.get('note_count', cluster.get('doc_count', 0))} 项\n"

    prompt += """
请输出JSON格式结果：
{
    "main_themes": ["主题1", "主题2"],
    "development_trends": ["趋势1", "趋势2"],
    "key_insights": ["洞察1", "洞察2"],
    "recommendations": ["建议1", "建议2"]
}

只输出JSON。
"""
    return json_request(prompt)


def deduplicate_entities(ttl_content: str) -> dict[str, Any]:
    """去重知识图谱实体"""
    prompt = f"""请从以下TTL知识图谱中提取所有唯一实体，并去除重复。

知识图谱内容：
{ttl_content}

请输出JSON格式结果：
{{
    "entities": ["实体1", "实体2", ...],
    "duplicates": {{"原始实体": "标准实体"}}
}}

只输出JSON。
"""
    return json_request(prompt)


def classify_and_draft(
    item: dict[str, Any],
    format_fn: Callable[[dict], str],
    fields: dict[str, str | list[str]],
) -> dict[str, Any]:
    """通用分类和起草"""
    prompt = f"""请分析以下内容，给出分类和总结。

{format_fn(item)}

请输出JSON格式结果：
{json.dumps({k: v for k, v in fields.items()}, ensure_ascii=False, indent=2)}

只输出JSON。
"""
    return json_request(prompt)

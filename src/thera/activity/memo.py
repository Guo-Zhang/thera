"""
备忘录活动

输入：`data/infra/apple/notes.json`

算法：
1. 使用 LLM 生成语义嵌入向量
2. 计算语义相似度并进行分组
3. 使用 LLM 抽取知识图谱三元组
4. 评估知识图谱质量
5. 生成分析报告

输出：`data/activity/memo/`
"""

import json
from pathlib import Path
from typing import Any

from thera.domain.knowl import (
    cluster_notes,
    embedding_similarity_matrix,
    extract_keywords,
    generate_report,
    generate_reasoning_report,
    get_embeddings,
)
from thera.infra.llm import (
    analyze_development_direction as llm_analyze_direction,
    classify_and_draft as llm_classify,
    evaluate_content_quality as llm_evaluate_content,
    evaluate_ttl_quality as llm_evaluate_ttl,
    extract_triplets as llm_extract_triplets,
    json_request as llm_json_request,
    summarize_content as llm_summarize_content,
)


def run_memo_activity(
    notes_file: Path,
    output_dir: Path,
    similarity_threshold: float = 0.5,
    enable_quality_check: bool = True,
) -> dict[str, Any]:
    """运行备忘录分析活动"""
    notes = load_notes(notes_file)
    if not notes:
        return {"error": "未找到备忘录数据"}

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"正在计算 {len(notes)} 条备忘录的嵌入...")
    texts = [n.get("title", "") + " " + n.get("body", "")[:1000] for n in notes]
    embeddings = get_embeddings(texts)

    print("正在计算相似度矩阵...")
    similarity_matrix = embedding_similarity_matrix(embeddings).tolist()

    print(f"正在分组 (阈值: {similarity_threshold})...")
    clusters_indices = cluster_notes(similarity_matrix, similarity_threshold)

    clusters = []
    ttl_content = ""
    quality_results = []

    content_intro = ""
    content_quality = {}

    if enable_quality_check:
        print("正在生成内容介绍...")
        content_intro = llm_summarize_content(
            notes,
            lambda n: f"标题: {n.get('title', '')}\n内容: {n.get('body', '')[:500]}",
            max_items=10,
            max_content=500,
            max_length=200,
        )

        print("正在评估内容质量...")
        content_quality = llm_evaluate_content(
            notes,
            lambda n: f"标题: {n.get('title', '')}\n内容: {n.get('body', '')[:600]}",
            {
                "completeness": "完整性：内容是否完整，有无断节",
                "clarity": "清晰度：表达是否清晰，逻辑是否连贯",
                "value": "价值性：内容是否有深度见解和实用价值",
                "organization": "组织性：标题和分类是否合理",
                "issues": "发现的问题",
                "suggestions": "改进建议",
            },
            max_items=8,
            max_content=600,
        )

        for idx, cluster in enumerate(clusters_indices[:3]):
            cluster_notes_list = [notes[i] for i in cluster]
            if not cluster_notes_list:
                continue

            ttl = llm_extract_triplets(
                cluster_notes_list,
                lambda n: f"标题: {n.get('title', '')}\n内容: {n.get('body', '')[:800]}",
                max_items=8,
                max_content=800,
            )
            ttl_content += f"\n# Cluster {idx + 1}\n{ttl}"

            titles = [n.get("title", "") for n in cluster_notes_list]
            quality = llm_evaluate_ttl(
                ttl,
                titles,
                {
                    "completeness": "完整性：是否覆盖了笔记的核心知识",
                    "accuracy": "准确性：实体和关系是否正确",
                    "coherence": "连贯性：知识之间是否形成有意义的关联",
                    "issues": "发现的问题",
                    "suggestions": "改进建议",
                },
            )
            quality_results.append(quality)

    ttl_file = output_dir / "knowledge.ttl"
    with open(ttl_file, "w", encoding="utf-8") as f:
        f.write(ttl_content)

    for idx, cluster_indices in enumerate(clusters_indices):
        cluster_notes_list = [notes[i] for i in cluster_indices]
        titles = [n.get("title", "") for n in cluster_notes_list]
        bodies = [n.get("body", "") for n in cluster_notes_list]
        keywords = extract_keywords(" ".join(bodies).split())

        cluster_quality = quality_results[idx] if idx < len(quality_results) else {}

        clusters.append(
            {
                "cluster_id": idx + 1,
                "note_count": len(cluster_indices),
                "titles": titles[:10],
                "keywords": keywords,
                "quality": cluster_quality,
            }
        )

    quality_template = {
        "completeness": ("完整性", "completeness"),
        "accuracy": ("准确性", "accuracy"),
        "coherence": ("连贯性", "coherence"),
    }

    report = generate_report(
        total_items=len(notes),
        clusters=clusters,
        ttl_file=ttl_file,
        quality_results=quality_results,
        output_dir=output_dir,
        title="备忘录分析报告",
        content_intro=content_intro,
        content_quality=content_quality,
        quality_template=quality_template,
        item_label="条笔记",
        cluster_label="分组",
    )

    report["clusters"] = clusters
    report["output_dir"] = str(output_dir)

    return report


def load_notes(notes_file: Path) -> list[dict[str, Any]]:
    """加载备忘录数据"""
    with open(notes_file, "r", encoding="utf-8") as f:
        return json.load(f)


def batch_classify_notes(notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """批量分类笔记"""
    results = []
    for i, note in enumerate(notes):
        if i % 10 == 0:
            print(f"  分类进度: {i}/{len(notes)}")
        result = llm_classify(
            note,
            lambda n: f"标题: {n.get('title', '')}\n内容: {n.get('body', '')}",
            {
                "category": "分类名称",
                "summary": "50字以内的总结",
                "keywords": ["关键词1", "关键词2"],
                "action_items": ["待办事项1"],
            },
        )
        results.append(result or {"error": "分类失败"})
    return results


def analyze_thinking_pattern(
    notes: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
) -> dict[str, Any]:
    """分析思维模式并给出维护建议"""
    prompt = f"""请分析以下备忘录的分类模式和内容特征，推测用户的思维模式，并给出维护建议。

备忘录总数: {len(notes)}
分组数: {len(clusters)}

各分组概述:
"""
    for cluster in clusters[:5]:
        titles = cluster.get("titles", [])[:5]
        keywords = cluster.get("keywords", [])[:5]
        prompt += (
            f"\n- 分组 {cluster['cluster_id']}: {cluster.get('note_count', 0)} 条笔记"
        )
        prompt += f"\n  标题示例: {', '.join(titles[:3])}"
        prompt += f"\n  关键词: {', '.join(keywords[:5])}"

    prompt += """

请分析并输出JSON格式结果：
{
    "thinking_pattern": {
        "type": "思维模式类型（如：系统化思维、创意型、战略型、分析型、综合型等）",
        "description": "思维模式描述"
    },
    "characteristics": [
        "特征1（如：喜欢分类归档）",
        "特征2（如：关注长远规划）"
    ],
    "strengths": [
        "优势1",
        "优势2"
    ],
    "blind_spots": [
        "盲点1",
        "盲点2"
    ],
    "maintenance_suggestions": [
        "建议1（如：建议每周整理一次）",
        "建议2（如：可以尝试新的分类维度）"
    ]
}

只输出JSON。
"""
    return llm_json_request(prompt)


def generate_thinking_report(
    thinking_analysis: dict[str, Any],
    output_dir: Path,
) -> str:
    """生成思维模式报告"""
    from datetime import datetime

    pattern = thinking_analysis.get("thinking_pattern", {})
    md = [
        "# 思维模式分析报告",
        "",
        f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 思维模式",
        "",
        f"**类型**: {pattern.get('type', '未知')}",
        "",
        pattern.get("description", ""),
        "",
        "## 特征分析",
        "",
    ]

    for char in thinking_analysis.get("characteristics", []):
        md.append(f"- {char}")

    md.extend(["", "## 优势", ""])
    for s in thinking_analysis.get("strengths", []):
        md.append(f"- {s}")

    md.extend(["", "## 盲点", ""])
    for b in thinking_analysis.get("blind_spots", []):
        md.append(f"- {b}")

    md.extend(["", "## 维护建议", ""])
    for s in thinking_analysis.get("maintenance_suggestions", []):
        md.append(f"- {s}")

    report_path = output_dir / "思维模式分析.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    return str(report_path)

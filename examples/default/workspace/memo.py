"""
备忘录活动 - 思维模式分析

输入：`data/infra/apple/notes.json`

功能：
1. 分析备忘录目录结构
2. 推测思维模式
3. 生成维护建议

输出：`data/activity/memo/`
"""

import json
from pathlib import Path
from typing import Any, Optional

from quanttide_agent import (
    analyze_development_direction as llm_analyze_direction,
    classify_and_draft as llm_classify,
    json_request as llm_json_request,
    summarize_content as llm_summarize_content,
)
from thera.mode.knowl import (
    cluster_notes,
    embedding_similarity_matrix,
    extract_keywords,
    generate_reasoning_report,
    get_embeddings,
)


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
        "type": "思维模式类型（如：系统化思维、创意型、战略型，分析型，综合型等）",
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


def run_memo_activity(
    notes_file: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    similarity_threshold: float = 0.5,
) -> dict[str, Any]:
    """运行备忘录分析活动"""
    if notes_file is None:
        notes_file = (
            Path(__file__).parent.parent.parent.parent
            / "data"
            / "infra"
            / "apple"
            / "notes.json"
        )
    if output_dir is None:
        output_dir = (
            Path(__file__).parent.parent.parent.parent / "data" / "activity" / "memo"
        )

    notes_file = Path(notes_file)
    output_dir = Path(output_dir)
    if not notes_file.exists():
        return {"error": f"备忘录文件不存在: {notes_file}"}

    notes = load_notes(notes_file)
    if not notes:
        return {"error": "未找到备忘录数据"}

    output_dir.mkdir(parents=True, exist_ok=True)

    texts = [n.get("title", "") + " " + n.get("body", "")[:500] for n in notes]
    embeddings = get_embeddings(texts)
    similarity_matrix = embedding_similarity_matrix(embeddings).tolist()

    clusters_indices = cluster_notes(similarity_matrix, similarity_threshold)

    clusters = []
    for idx, cluster_indices in enumerate(clusters_indices):
        cluster_notes_list = [notes[i] for i in cluster_indices]
        titles = [n.get("title", "") for n in cluster_notes_list]
        bodies = [n.get("body", "") for n in cluster_notes_list]
        keywords = extract_keywords(" ".join(bodies).split())

        clusters.append(
            {
                "cluster_id": idx + 1,
                "note_count": len(cluster_indices),
                "titles": titles[:10],
                "keywords": keywords,
            }
        )

    content_intro = llm_summarize_content(
        notes,
        lambda n: f"标题: {n.get('title', '')}\n内容: {n.get('body', '')[:300]}",
        max_items=10,
        max_content=300,
        max_length=200,
    )

    thinking_analysis = analyze_thinking_pattern(notes, clusters)

    report_path = generate_thinking_report(thinking_analysis, output_dir)

    with open(output_dir / "内容介绍.md", "w", encoding="utf-8") as f:
        f.write(f"# 备忘录内容介绍\n\n{content_intro}")

    return {
        "total_notes": len(notes),
        "total_clusters": len(clusters),
        "thinking_analysis": thinking_analysis,
        "report_path": report_path,
        "output_dir": str(output_dir),
    }


def load_notes(notes_file: Path) -> list[dict[str, Any]]:
    """加载备忘录数据"""
    with open(notes_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("notes", [])
    return data


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

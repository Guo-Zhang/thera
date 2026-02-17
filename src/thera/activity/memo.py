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
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from thera.config import settings
from thera.domain.knowl import (
    _parse_json_response,
    create_llm_client,
    embedding_similarity_matrix,
    get_embedding,
    get_embeddings,
    llm_chat_str,
    llm_json_request,
)


def compute_embeddings(notes: list[dict[str, Any]]) -> list[list[float]]:
    """计算笔记的语义嵌入向量"""
    texts = [
        note.get("title", "") + " " + note.get("body", "")[:1000] for note in notes
    ]
    return get_embeddings(texts).tolist()


def compute_similarity(embeddings: list[list[float]]) -> list[list[float]]:
    """计算相似度矩阵"""
    return embedding_similarity_matrix(embeddings).tolist()


def cluster_notes(
    similarity_matrix: list[list[float]],
    threshold: float = 0.5,
) -> list[list[int]]:
    """根据相似度阈值分组"""
    n = len(similarity_matrix)
    visited = [False] * n
    clusters = []

    for i in range(n):
        if visited[i]:
            continue

        cluster = [i]
        visited[i] = True

        for j in range(i + 1, n):
            if not visited[j] and similarity_matrix[i][j] > threshold:
                cluster.append(j)
                visited[j] = True

        if len(cluster) > 1:
            clusters.append(cluster)

    return clusters


def extract_triplets(notes_texts: list[dict[str, str]]) -> str:
    """使用 LLM 提取知识图谱三元组"""
    combined = "\n\n".join(
        [f"标题: {n['title']}\n内容: {n['body'][:800]}" for n in notes_texts[:8]]
    )

    prompt = f"""从以下备忘录文本中提取知识图谱三元组。
要求：
1. 提取实体和它们之间的关系
2. 关系用动词或介词短语表示
3. 只提取核心知识，忽略描述性内容

备忘录内容：
{combined}

请以以下TTL格式输出（只输出TTL，不要其他内容）：
@prefix kb: <http://example.org/knowledge/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

kb:实体1 rdfs:label "实体1" .
kb:实体2 rdfs:label "实体2" .
kb:实体1 kb:关系 kb:实体2 .
"""

    return llm_chat_str(prompt, temperature=0.3)


def evaluate_ttl_quality(ttl_content: str, notes_titles: list[str]) -> dict[str, Any]:
    """评估 TTL 知识图谱质量"""
    prompt = f"""请评估以下知识图谱的质量。

知识图谱TTL内容：
{ttl_content}

相关笔记标题：{notes_titles}

请从以下维度评估并输出JSON格式结果：
{{
    "completeness": 0-100,  // 完整性：是否覆盖了笔记的核心知识
    "accuracy": 0-100,       // 准确性：实体和关系是否正确
    "coherence": 0-100,      // 连贯性：知识之间是否形成有意义的关联
    "issues": ["问题1", "问题2"],  // 发现的问题
    "suggestions": ["建议1", "建议2"]  // 改进建议
}}

只输出JSON，不要其他内容。
"""

    result = llm_json_request(prompt)
    if not result:
        return {"error": "评估失败"}
    return result


def summarize_content(notes: list[dict[str, Any]]) -> str:
    """使用 LLM 生成内容介绍"""
    sample_notes = notes[:10]
    combined = "\n\n".join(
        [
            f"标题: {n.get('title', '')}\n内容: {n.get('body', '')[:500]}"
            for n in sample_notes
        ]
    )

    prompt = f"""请为以下备忘录内容生成一个简洁的介绍（200字以内）。

备忘录内容：
{combined}

请直接输出介绍内容，不要其他格式。
"""

    return llm_chat_str(prompt, temperature=0.3)


def evaluate_content_quality(notes: list[dict[str, Any]]) -> dict[str, Any]:
    """评估备忘录内容质量"""
    sample_notes = notes[:8]
    combined = "\n\n".join(
        [
            f"标题: {n.get('title', '')}\n内容: {n.get('body', '')[:600]}"
            for n in sample_notes
        ]
    )

    prompt = f"""请评估以下备忘录内容的质量。

备忘录内容：
{combined}

请从以下维度评估并输出JSON格式结果：
{{
    "completeness": 0-100,  // 完整性：内容是否完整，有无断节
    "clarity": 0-100,       // 清晰度：表达是否清晰，逻辑是否连贯
    "value": 0-100,         // 价值性：内容是否有深度见解和实用价值
    "organization": 0-100,  // 组织性：标题和分类是否合理
    "issues": ["问题1", "问题2"],  // 发现的问题
    "suggestions": ["建议1", "建议2"]  // 改进建议
}}

只输出JSON，不要其他内容。
"""

    result = llm_json_request(prompt)
    if not result:
        return {"error": "评估失败"}
    return result


def generate_report(
    total_notes: int,
    clusters: list[dict[str, Any]],
    ttl_file: Path,
    quality_results: list[dict[str, Any]],
    output_dir: Path,
    notes: list[dict[str, Any]] | None = None,
    content_intro: str | None = None,
    content_quality: dict[str, Any] | None = None,
    similarity_threshold: float = 0.5,
    enable_quality_check: bool = True,
) -> dict[str, Any]:
    """生成分析报告"""
    avg_completeness = (
        sum(q.get("completeness", 0) for q in quality_results) / len(quality_results)
        if quality_results
        else 0
    )
    avg_accuracy = (
        sum(q.get("accuracy", 0) for q in quality_results) / len(quality_results)
        if quality_results
        else 0
    )
    avg_coherence = (
        sum(q.get("coherence", 0) for q in quality_results) / len(quality_results)
        if quality_results
        else 0
    )

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_notes": total_notes,
        "total_clusters": len(clusters),
    }

    md_report = [
        "# 备忘录分析报告",
        "",
        f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **备忘录总数**: {total_notes}",
        f"- **发现分组数**: {len(clusters)}",
        "",
    ]

    if content_intro:
        md_report.extend(
            [
                "## 内容介绍",
                "",
                content_intro,
                "",
            ]
        )

    for cluster in clusters:
        cid = cluster["cluster_id"]
        md_report.extend(
            [
                f"## 分组 {cid}: {cluster['note_count']} 条笔记",
                "",
                "**笔记标题:**",
            ]
        )
        for title in cluster["titles"]:
            md_report.append(f"- {title}")
        md_report.extend(
            [
                "",
                "**关键词:**",
                ", ".join(cluster.get("keywords", [])[:10]),
                "",
                "---",
                "",
            ]
        )

    md_report.append(f"*知识图谱已保存至: {ttl_file.name}*")

    with open(output_dir / "报告.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_report))

    md_eval = [
        "# 备忘录分析评估",
        "",
        f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **备忘录总数**: {total_notes}",
        f"- **发现分组数**: {len(clusters)}",
        "",
    ]

    if content_quality and not content_quality.get("error"):
        md_eval.extend(
            [
                "## 内容质量评估",
                "",
                f"| 维度 | 分数 |",
                f"| --- | --- |",
                f"| 完整性 (Completeness) | {content_quality.get('completeness', '-')} |",
                f"| 清晰度 (Clarity) | {content_quality.get('clarity', '-')} |",
                f"| 价值性 (Value) | {content_quality.get('value', '-')} |",
                f"| 组织性 (Organization) | {content_quality.get('organization', '-')} |",
                "",
            ]
        )
        if content_quality.get("issues"):
            md_eval.append("**问题:**")
            for issue in content_quality.get("issues", []):
                md_eval.append(f"- {issue}")
            md_eval.append("")
        if content_quality.get("suggestions"):
            md_eval.append("**改进建议:**")
            for suggestion in content_quality.get("suggestions", []):
                md_eval.append(f"- {suggestion}")
            md_eval.append("")

    md_eval.extend(
        [
            "## 知识图谱质量评估",
            "",
            f"| 维度 | 分数 |",
            f"| --- | --- |",
            f"| 完整性 (Completeness) | {avg_completeness:.1f} |",
            f"| 准确性 (Accuracy) | {avg_accuracy:.1f} |",
            f"| 连贯性 (Coherence) | {avg_coherence:.1f} |",
            "",
        ]
    )

    for cluster in clusters:
        cid = cluster["cluster_id"]
        quality = cluster.get("quality", {})
        if quality and not quality.get("error"):
            md_eval.extend(
                [
                    f"### 分组 {cid} 质量",
                    "",
                    f"| 维度 | 分数 |",
                    f"| --- | --- |",
                    f"| 完整性 | {quality.get('completeness', '-')} |",
                    f"| 准确性 | {quality.get('accuracy', '-')} |",
                    f"| 连贯性 | {quality.get('coherence', '-')} |",
                    "",
                ]
            )

    with open(output_dir / "评估.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_eval))

    return report


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
    embeddings = compute_embeddings(notes)

    print("正在计算相似度矩阵...")
    similarity_matrix = compute_similarity(embeddings)

    print(f"正在分组 (阈值: {similarity_threshold})...")
    clusters_indices = cluster_notes(similarity_matrix, similarity_threshold)

    clusters = []
    ttl_content = ""
    quality_results = []

    content_intro = ""
    content_quality = {}

    if enable_quality_check:
        print("正在生成内容介绍...")
        content_intro = summarize_content(notes)

        print("正在评估内容质量...")
        content_quality = evaluate_content_quality(notes)

        cluster_notes_for_ttl = [
            [notes[i] for i in cluster] for cluster in clusters_indices[:3]
        ]

        for cluster_idx, cluster_note_list in enumerate(cluster_notes_for_ttl):
            if not cluster_note_list:
                continue

            ttl = extract_triplets(cluster_note_list)
            ttl_content += f"\n# Cluster {cluster_idx + 1}\n{ttl}"

            if enable_quality_check:
                titles = [n.get("title", "") for n in cluster_note_list]
                quality = evaluate_ttl_quality(ttl, titles)
                quality_results.append(quality)

    ttl_file = output_dir / "knowledge.ttl"
    with open(ttl_file, "w", encoding="utf-8") as f:
        f.write(ttl_content)

    for idx, cluster_indices in enumerate(clusters_indices):
        cluster_notes_list = [notes[i] for i in cluster_indices]
        titles = [n.get("title", "") for n in cluster_notes_list]
        bodies = [n.get("body", "") for n in cluster_notes_list]
        keywords = _extract_keywords(" ".join(bodies))

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

    report = generate_report(
        total_notes=len(notes),
        clusters=clusters,
        ttl_file=ttl_file,
        quality_results=quality_results,
        output_dir=output_dir,
        content_intro=content_intro,
        content_quality=content_quality,
        similarity_threshold=similarity_threshold,
        enable_quality_check=enable_quality_check,
    )

    report["clusters"] = clusters
    report["output_dir"] = str(output_dir)

    return report


def load_notes(notes_file: Path) -> list[dict[str, Any]]:
    """加载备忘录数据"""
    with open(notes_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_keywords(text: str) -> list[str]:
    """提取关键词"""
    import re

    words = re.findall(r"[\w]{2,}", text)
    counter = Counter(words)
    return [word for word, _ in counter.most_common(20)]


def compute_cluster_centroids(
    embeddings: list[list[float]], clusters: list[list[int]]
) -> list[list[float]]:
    """计算每个聚类的质心"""
    import numpy as np

    embeddings_array = np.array(embeddings)
    centroids = []
    for cluster in clusters:
        cluster_embeddings = embeddings_array[cluster]
        centroid = cluster_embeddings.mean(axis=0).tolist()
        centroids.append(centroid)
    return centroids


def find_bridge_notes(
    embeddings: list[list[float]], clusters: list[list[int]], threshold: float = 0.3
) -> list[dict[str, Any]]:
    """找出连接不同聚类的桥接笔记"""
    import numpy as np

    embeddings_array = np.array(embeddings)
    centroids = compute_cluster_centroids(embeddings, clusters)
    n_clusters = len(clusters)

    if n_clusters < 2:
        return []

    bridge_notes = []
    for i, cluster in enumerate(clusters):
        for note_idx in cluster:
            note_embedding = embeddings_array[note_idx]
            similarities = []
            for j, centroid in enumerate(centroids):
                if i == j:
                    continue
                sim = np.dot(note_embedding, centroid) / (
                    np.linalg.norm(note_embedding) * np.linalg.norm(centroid) + 1e-8
                )
                similarities.append((j, sim))

            max_sim = max(similarities, key=lambda x: x[1])
            if max_sim[1] > threshold:
                bridge_notes.append(
                    {
                        "note_index": note_idx,
                        "from_cluster": i,
                        "to_cluster": max_sim[0],
                        "similarity": float(max_sim[1]),
                    }
                )

    return bridge_notes


def find_cross_cluster_links(
    embeddings: list[list[float]], clusters: list[list[int]], top_n: int = 3
) -> list[dict[str, Any]]:
    """找出跨聚类的高相似度连接"""
    import numpy as np

    embeddings_array = np.array(embeddings)
    n_clusters = len(clusters)
    cross_links = []

    for i in range(n_clusters):
        for j in range(i + 1, n_clusters):
            cluster_i_embeddings = embeddings_array[clusters[i]]
            cluster_j_embeddings = embeddings_array[clusters[j]]

            sim_matrix = np.dot(cluster_i_embeddings, cluster_j_embeddings.T)
            sim_matrix = sim_matrix / (
                np.linalg.norm(cluster_i_embeddings, axis=1, keepdims=True)
                * np.linalg.norm(cluster_j_embeddings, axis=1, keepdims=True).T
                + 1e-8
            )

            for _ in range(top_n):
                max_idx = np.unravel_index(np.argmax(sim_matrix), sim_matrix.shape)
                max_sim = sim_matrix[max_idx]
                if max_sim > 0.5:
                    cross_links.append(
                        {
                            "from_cluster": i,
                            "to_cluster": j,
                            "from_note": clusters[i][max_idx[0]],
                            "to_note": clusters[j][max_idx[1]],
                            "similarity": float(max_sim),
                        }
                    )
                    sim_matrix[max_idx[0], max_idx[1]] = 0
                else:
                    break

    return cross_links


def deduplicate_entities(ttl_content: str) -> dict[str, Any]:
    """使用 LLM 去重知识图谱实体"""
    prompt = f"""请从以下TTL知识图谱中提取所有唯一实体，并去除重复。

知识图谱内容：
{ttl_content}

请输出JSON格式结果：
{{
    "entities": ["实体1", "实体2", ...],  // 唯一实体列表
    "duplicates": {{"原始实体": "标准实体"}}  // 重复映射
}}

只输出JSON。
"""

    return llm_json_request(prompt)


def classify_and_draft_note(note: dict[str, Any]) -> dict[str, Any]:
    """使用 LLM 分类和起草笔记"""
    prompt = f"""请分析以下备忘录，给出分类和总结。

标题: {note.get("title", "")}
内容: {note.get("body", "")}

请输出JSON格式结果：
{{
    "category": "分类名称",
    "summary": "50字以内的总结",
    "keywords": ["关键词1", "关键词2"],
    "action_items": ["待办事项1", "待办事项2"]  // 如果有
}}

只输出JSON。
"""

    result = llm_json_request(prompt)
    if not result:
        return {"error": "分类失败"}
    return result


def batch_classify_notes(notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """批量分类笔记"""
    results = []
    for i, note in enumerate(notes):
        if i % 10 == 0:
            print(f"  分类进度: {i}/{len(notes)}")
        result = classify_and_draft_note(note)
        results.append(result)
    return results


def analyze_development_direction(
    notes: list[dict[str, Any]], clusters: list[dict[str, Any]]
) -> dict[str, Any]:
    """分析备忘录的发展方向"""
    category_prompt = f"""请分析以下备忘录集合的发展方向和趋势。

备忘录总数: {len(notes)}
分组数: {len(clusters)}

"""

    if clusters:
        category_prompt += "各分组概述:\n"
        for cluster in clusters[:5]:
            category_prompt += f"- 分组 {cluster['cluster_id']}: {cluster.get('note_count', 0)} 条笔记\n"

    category_prompt += """
请输出JSON格式结果：
{
    "main_themes": ["主题1", "主题2"],
    "development_trends": ["趋势1", "趋势2"],
    "key_insights": ["洞察1", "洞察2"],
    "recommendations": ["建议1", "建议2"]
}

只输出JSON。
"""

    result = llm_json_request(category_prompt)
    if not result:
        return {"error": "分析失败"}
    return result


def generate_reasoning_report(
    direction_analysis: dict[str, Any],
    clusters: list[dict[str, Any]],
    output_dir: Path,
) -> str:
    """生成推理报告"""
    md = [
        "# 备忘录发展方向推理报告",
        "",
        f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **分组数**: {len(clusters)}",
        "",
    ]

    if direction_analysis.get("main_themes"):
        md.extend(
            [
                "## 主要主题",
                "",
            ]
        )
        for theme in direction_analysis["main_themes"]:
            md.append(f"- {theme}")
        md.append("")

    if direction_analysis.get("development_trends"):
        md.extend(
            [
                "## 发展趋势",
                "",
            ]
        )
        for trend in direction_analysis["development_trends"]:
            md.append(f"- {trend}")
        md.append("")

    if direction_analysis.get("key_insights"):
        md.extend(
            [
                "## 关键洞察",
                "",
            ]
        )
        for insight in direction_analysis["key_insights"]:
            md.append(f"- {insight}")
        md.append("")

    if direction_analysis.get("recommendations"):
        md.extend(
            [
                "## 建议",
                "",
            ]
        )
        for rec in direction_analysis["recommendations"]:
            md.append(f"- {rec}")
        md.append("")

    report_path = output_dir / "发展方向推理.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    return str(report_path)

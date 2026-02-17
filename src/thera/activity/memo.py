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
    get_embeddings,
)
from thera.infra.llm import (
    chat_str as llm_chat_str,
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
    prompt = f"""请分析以下备忘录集合的发展方向和趋势。

备忘录总数: {len(notes)}
分组数: {len(clusters)}

"""
    if clusters:
        prompt += "各分组概述:\n"
        for cluster in clusters[:5]:
            prompt += f"- 分组 {cluster['cluster_id']}: {cluster.get('note_count', 0)} 条笔记\n"

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
    result = llm_json_request(prompt)
    if not result:
        return {"error": "分析失败"}
    return result


def generate_reasoning_report(
    direction_analysis: dict[str, Any],
    clusters: list[dict[str, Any]],
    output_dir: Path,
) -> str:
    """生成推理报告"""
    from datetime import datetime

    md = [
        "# 备忘录发展方向推理报告",
        "",
        f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **分组数**: {len(clusters)}",
        "",
    ]

    if direction_analysis.get("main_themes"):
        md.extend(["## 主要主题", ""])
        for theme in direction_analysis["main_themes"]:
            md.append(f"- {theme}")
        md.append("")

    if direction_analysis.get("development_trends"):
        md.extend(["## 发展趋势", ""])
        for trend in direction_analysis["development_trends"]:
            md.append(f"- {trend}")
        md.append("")

    if direction_analysis.get("key_insights"):
        md.extend(["## 关键洞察", ""])
        for insight in direction_analysis["key_insights"]:
            md.append(f"- {insight}")
        md.append("")

    if direction_analysis.get("recommendations"):
        md.extend(["## 建议", ""])
        for rec in direction_analysis["recommendations"]:
            md.append(f"- {rec}")
        md.append("")

    report_path = output_dir / "发展方向推理.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    return str(report_path)

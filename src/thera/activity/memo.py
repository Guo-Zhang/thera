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
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import OpenAI

from thera.config import settings


def create_llm_client() -> OpenAI:
    """创建 LLM 客户端"""
    return OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)


def get_embedding(text: str, client: OpenAI) -> list[float]:
    """使用 OpenAI 获取文本嵌入"""
    response = client.embeddings.create(
        model=settings.llm_embedding_model,
        input=text,
    )
    return response.data[0].embedding


def compute_embeddings(
    notes: list[dict[str, Any]], client: OpenAI
) -> list[list[float]]:
    """计算笔记的语义嵌入向量"""
    embeddings = []

    for i, note in enumerate(notes):
        text = note.get("title", "") + " " + note.get("body", "")[:1000]

        if i % 5 == 0:
            print(f"  嵌入进度: {i}/{len(notes)}")

        embedding = get_embedding(text, client)
        embeddings.append(embedding)

    return embeddings


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """计算余弦相似度"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    return dot / (norm_a * norm_b) if norm_a * norm_b > 0 else 0


def compute_similarity(embeddings: list[list[float]]) -> list[list[float]]:
    """计算相似度矩阵"""
    n = len(embeddings)
    matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(1.0)
            else:
                row.append(cosine_similarity(embeddings[i], embeddings[j]))
        matrix.append(row)
    return matrix


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


def extract_triplets(client: OpenAI, notes_texts: list[dict[str, str]]) -> str:
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

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    return content if content else ""


def evaluate_ttl_quality(
    client: OpenAI, ttl_content: str, notes_titles: list[str]
) -> dict[str, Any]:
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

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    if not content:
        return {"error": "评估失败"}

    try:
        import json

        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
    except Exception:
        pass

    return {"error": "解析失败", "raw": content}


def summarize_content(client: OpenAI, notes: list[dict[str, Any]]) -> str:
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

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    return content.strip() if content else ""


def evaluate_content_quality(
    client: OpenAI, notes: list[dict[str, Any]]
) -> dict[str, Any]:
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

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    if not content:
        return {"error": "评估失败"}

    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
    except Exception:
        pass

    return {"error": "解析失败", "raw": content}


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
                    f"### 分组 {cid} 知识图谱评估",
                    "",
                    f"- 完整性: {quality.get('completeness', '-')}",
                    f"- 准确性: {quality.get('accuracy', '-')}",
                    f"- 连贯性: {quality.get('coherence', '-')}",
                    "",
                ]
            )
            if quality.get("issues"):
                md_eval.append("**问题:**")
                for issue in quality.get("issues", []):
                    md_eval.append(f"- {issue}")
                md_eval.append("")
            if quality.get("suggestions"):
                md_eval.append("**改进建议:**")
                for suggestion in quality.get("suggestions", []):
                    md_eval.append(f"- {suggestion}")
                md_eval.append("")

    with open(output_dir / "评估.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_eval))

    md_review = [
        "# 备忘录分析复盘",
        "",
        f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **备忘录总数**: {total_notes}",
        f"- **发现分组数**: {len(clusters)}",
        "",
        "## 算法流程",
        "",
        "1. **语义嵌入**: 使用 OpenAI Embedding API 获取文本语义向量",
        "2. **相似度计算**: 使用余弦相似度计算笔记之间的相似度",
        "3. **分组聚类**: 基于相似度阈值(0.5)进行聚类",
        "4. **知识抽取**: 使用 LLM 提取知识图谱三元组",
        "5. **质量评估**: 使用 LLM 评估知识图谱质量",
        "",
        "## 参数配置",
        "",
        f"- 相似度阈值: {similarity_threshold}",
        f"- 质量评估: {'启用' if enable_quality_check else '禁用'}",
        "",
        "## 经验总结",
        "",
        "### 1. 语义相似度 vs 词频相似度",
        "",
        "使用语义嵌入(Embedding)比 TF-IDF 更能理解内容的实际含义，",
        "能够发现词面不相似但语义相关的笔记。",
        "",
        "### 2. 知识图谱 TTL 格式",
        "",
        "使用标准 RDF Turtle 格式，便于后续知识图谱的存储和查询。",
        "每个实体使用 rdfs:label 标注中文名称。",
        "",
        "### 3. LLM 评估的局限性",
        "",
        "LLM 评估倾向于给出中等分数，且评估标准可能过于严格。",
        "建议结合人工审核来确认评估结果。",
        "",
        "### 4. 分组数量与阈值",
        "",
        "相似度阈值 0.5 适用于中等相似度的笔记分组。",
        "阈值过高会导致分组过少，阈值过低会使得分组过多且不相关。",
        "",
    ]

    with open(output_dir / "复盘.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_review))

    return report


def run_memo_activity(
    notes_file: Path | None = None,
    output_dir: Path | None = None,
    similarity_threshold: float = 0.5,
    enable_quality_check: bool = True,
) -> dict[str, Any]:
    """运行备忘录活动

    Args:
        notes_file: 备忘录数据文件路径
        output_dir: 输出目录
        similarity_threshold: 相似度阈值
        enable_quality_check: 是否启用质量评估
    """
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

    output_dir.mkdir(parents=True, exist_ok=True)

    client = create_llm_client()

    notes = load_notes(notes_file)
    print(f"加载了 {len(notes)} 条备忘录")

    print("计算语义嵌入向量...")
    embeddings = compute_embeddings(notes, client)
    print(f"计算了 {len(embeddings)} 个嵌入向量")

    similarity_matrix = compute_similarity(embeddings)

    vector_data = {
        "notes": [
            {"index": i, "title": notes[i].get("title", "")} for i in range(len(notes))
        ],
        "embeddings": embeddings,
        "similarity_matrix": similarity_matrix,
    }
    vector_file = output_dir / "vectors.json"
    with open(vector_file, "w", encoding="utf-8") as f:
        json.dump(vector_data, f, ensure_ascii=False)
    print(f"向量数据已保存到: {vector_file}")

    clusters = cluster_notes(similarity_matrix, threshold=similarity_threshold)
    print(f"发现 {len(clusters)} 个分组")

    ttl_lines = [
        "@prefix kb: <http://example.org/knowledge/> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "",
    ]

    cluster_results = []
    quality_results = []

    for idx, cluster in enumerate(clusters):
        cluster_notes_list = [notes[i] for i in cluster]
        titles = [n.get("title", "") for n in cluster_notes_list]

        print(f"  处理 Cluster {idx + 1} ({len(cluster)} notes)...")

        ttl_triplets = extract_triplets(client, cluster_notes_list)

        ttl_lines.append(f"# Cluster {idx + 1}: {len(cluster)} related notes")
        ttl_lines.append(ttl_triplets)
        ttl_lines.append("")

        quality = {}
        if enable_quality_check and ttl_triplets:
            print(f"    评估质量...")
            quality = evaluate_ttl_quality(client, ttl_triplets, titles)
            quality_results.append(
                {
                    "cluster_id": idx + 1,
                    **quality,
                }
            )

        cluster_results.append(
            {
                "cluster_id": idx + 1,
                "note_count": len(cluster),
                "titles": titles,
                "keywords": _extract_keywords(titles),
                "quality": quality,
            }
        )

    ttl_file = output_dir / "knowledge.ttl"
    with open(ttl_file, "w", encoding="utf-8") as f:
        f.write("\n".join(ttl_lines))
    print(f"知识图谱已保存到: {ttl_file}")

    print("发现跨组关联...")
    cross_links = find_cross_cluster_links(embeddings, clusters, notes)
    with open(output_dir / "跨组关联.json", "w", encoding="utf-8") as f:
        json.dump(cross_links, f, ensure_ascii=False, indent=2)
    print(f"发现 {len(cross_links)} 个跨组关联")

    print("实体消歧...")
    combined_ttl = "\n".join(ttl_lines)
    dedup_result = deduplicate_entities(client, combined_ttl)
    if dedup_result:
        with open(output_dir / "术语映射表.json", "w", encoding="utf-8") as f:
            json.dump(dedup_result, f, ensure_ascii=False, indent=2)
        print(f"消歧完成，{len(dedup_result.get('mapping', {}))} 个映射")

    print("意图分类与卡片生成...")
    card_results = batch_classify_notes(client, notes)
    with open(output_dir / "知识卡片草稿.json", "w", encoding="utf-8") as f:
        json.dump(card_results, f, ensure_ascii=False, indent=2)

    md_cards = ["# 知识卡片集\n\n"]
    intent_counts = {}
    for d in card_results:
        intent = d.get("primary_intent", "Unknown")
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
        draft = d.get("card_draft", {})
        if draft:
            md_cards.append(
                f"## {draft.get('title', d.get('original_title', 'Untitled'))}\n\n"
            )
            md_cards.append(f"**意图**: {intent}\n\n")
            md_cards.append(f"**摘要**: {draft.get('summary', '')}\n\n")
            if draft.get("key_points"):
                md_cards.append("### 要点\n\n")
                for p in draft.get("key_points", []):
                    md_cards.append(f"- {p}\n")
                md_cards.append("\n")
            md_cards.append("---\n\n")

    with open(output_dir / "知识卡片集.md", "w", encoding="utf-8") as f:
        f.writelines(md_cards)
    print(f"生成 {len(card_results)} 张知识卡片")
    print(f"意图分布: {intent_counts}")

    generate_reasoning_report(
        client, notes, cluster_results, cross_links, card_results, output_dir
    )

    print("生成内容介绍...")
    content_intro = summarize_content(client, notes)

    print("评估内容质量...")
    content_quality = {}
    if enable_quality_check:
        content_quality = evaluate_content_quality(client, notes)

    report = generate_report(
        len(notes),
        cluster_results,
        ttl_file,
        quality_results,
        output_dir,
        notes=notes,
        content_intro=content_intro,
        content_quality=content_quality,
        similarity_threshold=similarity_threshold,
        enable_quality_check=enable_quality_check,
    )
    print(f"分析报告已保存到: {output_dir / '报告.md'}")

    return report


def load_notes(notes_file: Path) -> list[dict[str, Any]]:
    """加载备忘录数据"""
    with open(notes_file, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("notes", [])


def _extract_keywords(texts: list[str]) -> list[str]:
    """提取关键词"""
    all_text = " ".join(texts)
    words = re.findall(r"[\u4e00-\u9fa5]{2,4}", all_text)
    counter = Counter(words)
    return [w for w, _ in counter.most_common(15)]


def compute_cluster_centroids(
    embeddings: list[list[float]], clusters: list[list[int]]
) -> list[list[float]]:
    """计算每个分组的质心向量"""
    centroids = []
    for cluster_indices in clusters:
        cluster_vectors = [embeddings[i] for i in cluster_indices]
        centroid = [sum(v) / len(v) for v in zip(*cluster_vectors)]
        centroids.append(centroid)
    return centroids


def find_bridge_notes(
    embeddings: list[list[float]],
    cluster_indices: list[int],
    centroid_b: list[float],
    notes: list[dict[str, Any]],
    top_k: int = 2,
) -> list[dict[str, Any]]:
    """找出连接两个分组的桥梁笔记"""
    scores = []
    for idx in cluster_indices:
        sim = cosine_similarity(embeddings[idx], centroid_b)
        scores.append((idx, sim))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [
        {
            "title": notes[idx].get("title", ""),
            "index": idx,
            "similarity": round(sim, 3),
        }
        for idx, sim in scores[:top_k]
    ]


def find_cross_cluster_links(
    embeddings: list[list[float]],
    clusters: list[list[int]],
    notes: list[dict[str, Any]],
    threshold: float = 0.4,
) -> list[dict[str, Any]]:
    """发现跨组关联"""
    centroids = compute_cluster_centroids(embeddings, clusters)
    cross_links = []

    for i in range(len(clusters)):
        for j in range(i + 1, len(clusters)):
            sim = cosine_similarity(centroids[i], centroids[j])
            if sim > threshold:
                bridge_notes_a = find_bridge_notes(
                    embeddings, clusters[i], centroids[j], notes
                )
                bridge_notes_b = find_bridge_notes(
                    embeddings, clusters[j], centroids[i], notes
                )
                cross_links.append(
                    {
                        "group_a": i + 1,
                        "group_b": j + 1,
                        "similarity": round(sim, 3),
                        "bridge_from_a": bridge_notes_a,
                        "bridge_from_b": bridge_notes_b,
                    }
                )

    return cross_links


def deduplicate_entities(client: OpenAI, ttl_content: str) -> dict[str, Any]:
    """从 TTL 中提取实体并进行消歧"""
    entities = list(set(re.findall(r'rdfs:label\s+"([^"]+)"', ttl_content)))
    if not entities:
        return {}

    entity_list = "\n".join(entities[:50])
    prompt = f"""你是一个知识图谱专家。请分析以下从备忘录中提取的实体列表。
有些实体虽然名称不同，但指代的是同一个概念（例如"IAM"和"身份与访问管理"）。
请根据你的知识判断，生成一份映射表。

实体列表：
{entity_list}

请以 JSON 格式输出映射关系：
{{
  "canonical_entities": ["实体A", "实体B", ...],
  "mapping": {{
    "别名": "标准名称"
  }}
}}
只输出JSON，不要其他内容。
"""
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )

    content = response.choices[0].message.content
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
    except Exception:
        pass
    return {}


def classify_and_draft_note(client: OpenAI, note: dict[str, Any]) -> dict[str, Any]:
    """分类并生成卡片草稿"""
    prompt = f"""请分析以下备忘录内容，判断其主要意图类型。

标题：{note.get("title", "")}
正文：{note.get("body", "")[:1000]}

意图类型定义：
- Definition: 定义概念、解释术语、阐述原理
- Action: 待办事项、任务计划、行动步骤
- Case: 具体案例、实验记录、故事片段
- Question: 疑问、困惑、需要解决的问题
- Insight: 顿悟、灵感、核心观点

请输出 JSON：
{{
  "primary_intent": "意图类型",
  "card_draft": {{
    "title": "提炼后的正式标题",
    "summary": "一句话核心摘要",
    "key_points": ["要点1", "要点2"]
  }}
}}
只输出JSON，不要其他内容。
"""
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
    except Exception:
        pass
    return {"primary_intent": "Unknown", "card_draft": {}}


def batch_classify_notes(
    client: OpenAI, notes: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """批量分类笔记意图并生成草稿"""
    results = []
    for i, note in enumerate(notes):
        if i % 5 == 0:
            print(f"  意图分类进度: {i}/{len(notes)}")
        res = classify_and_draft_note(client, note)
        results.append(
            {
                "original_title": note.get("title"),
                "index": i,
                **res,
            }
        )
    return results


def analyze_development_direction(
    client: OpenAI,
    notes: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    cross_links: list[dict[str, Any]],
    card_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """分析编程开发方向"""

    dev_related_notes = []
    for note in notes:
        title = note.get("title", "").lower()
        body = note.get("body", "").lower()
        keywords = [
            "编程",
            "代码",
            "软件",
            "开发",
            "系统",
            "架构",
            "api",
            "算法",
            "模型",
            "ai",
            "llm",
            "agent",
            "智能体",
            "rag",
            "知识图谱",
            "neo4j",
            "embedding",
        ]
        if any(kw in title or kw in body for kw in keywords):
            dev_related_notes.append(note)

    prompt = f"""你是一个资深技术架构师和AI产品专家。请分析以下备忘录内容，推理出具体的编程开发方向和实现路径。

要求：
1. 从备忘录中提取与编程开发相关的核心概念
2. 分析这些概念之间的关联
3. 给出具体的技术选型建议
4. 规划实现路径优先级

相关笔记数量：{len(dev_related_notes)}

笔记内容：
"""

    for i, note in enumerate(dev_related_notes[:15]):
        prompt += f"\n{i + 1}. {note.get('title', '')}\n{note.get('body', '')[:500]}\n"

    prompt += """
请输出JSON格式的建议：
{
  "core_concepts": ["概念1", "概念2", ...],
  "technical_stack": {
    "recommended": ["技术1", "技术2"],
    "alternatives": ["备选1", "备选2"]
  },
  "implementation_phases": [
    {
      "phase": "阶段1",
      "description": "描述",
      "priority": 1-5,
      "key_tasks": ["任务1", "任务2"]
    }
  ],
  "risks": ["风险1", "风险2"],
  "opportunities": ["机会1", "机会2"]
}
只输出JSON，不要其他内容。
"""

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
    except Exception:
        pass
    return {}


def generate_reasoning_report(
    client: OpenAI,
    notes: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    cross_links: list[dict[str, Any]],
    card_results: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    """生成推理报告"""
    print("分析开发方向...")
    dev_analysis = analyze_development_direction(
        client, notes, clusters, cross_links, card_results
    )

    md_lines = [
        "# 编程开发方向推理报告",
        "",
        f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **分析笔记数**: {len(notes)}",
        "",
    ]

    if dev_analysis:
        if dev_analysis.get("core_concepts"):
            md_lines.extend(
                [
                    "## 核心概念",
                    "",
                    ", ".join(dev_analysis["core_concepts"]),
                    "",
                ]
            )

        if dev_analysis.get("technical_stack"):
            stack = dev_analysis["technical_stack"]
            md_lines.extend(
                [
                    "## 技术选型",
                    "",
                    "**推荐技术:** " + ", ".join(stack.get("recommended", [])),
                    "",
                    "**备选技术:** " + ", ".join(stack.get("alternatives", [])),
                    "",
                ]
            )

        if dev_analysis.get("implementation_phases"):
            md_lines.append("## 实现路径")
            md_lines.append("")
            for phase in dev_analysis["implementation_phases"]:
                priority = phase.get("priority", 0)
                star = "⭐" * (6 - priority)
                md_lines.append(f"### {phase.get('phase', '')} {star}")
                md_lines.append("")
                md_lines.append(phase.get("description", ""))
                md_lines.append("")
                md_lines.append("**关键任务:**")
                for task in phase.get("key_tasks", []):
                    md_lines.append(f"- {task}")
                md_lines.append("")

        if dev_analysis.get("risks"):
            md_lines.extend(
                [
                    "## 风险与挑战",
                    "",
                ]
            )
            for risk in dev_analysis["risks"]:
                md_lines.append(f"- {risk}")
            md_lines.append("")

        if dev_analysis.get("opportunities"):
            md_lines.extend(
                [
                    "## 机会与价值",
                    "",
                ]
            )
            for opp in dev_analysis["opportunities"]:
                md_lines.append(f"- {opp}")
            md_lines.append("")

        with open(output_dir / "推理报告.md", "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        with open(output_dir / "开发方向分析.json", "w", encoding="utf-8") as f:
            json.dump(dev_analysis, f, ensure_ascii=False, indent=2)

        print(f"推理报告已保存")
    else:
        print("推理分析失败")


if __name__ == "__main__":
    run_memo_activity()

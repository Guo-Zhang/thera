"""
知识发现活动

输入：`data/infra/github/` (quanttide-profile-of-founder 知识库)

算法：
1. 扫描知识库目录，加载所有 Markdown 文件
2. 使用 LLM 生成语义嵌入向量
3. 计算语义相似度并进行分组
4. 使用 LLM 抽取知识图谱三元组
5. 评估知识图谱质量
6. 生成分析报告

输出：`data/activity/profile/`
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


def scan_knowledge_base(base_dir: Path) -> list[dict[str, Any]]:
    """扫描知识库目录，加载所有 Markdown 文件"""
    docs = []
    categories = [
        "think",
        "agent",
        "knowl",
        "learn",
        "stdn",
        "write",
        "connect",
        "code",
        "brand",
        "acad",
        "product",
    ]

    for category in categories:
        category_dir = base_dir / category
        if not category_dir.exists():
            continue

        for md_file in category_dir.glob("*.md"):
            if md_file.name == "index.md":
                continue

            try:
                content = md_file.read_text(encoding="utf-8")
                first_line = content.split("\n")[0] if content else ""
                title = (
                    first_line.lstrip("# ").strip()
                    if first_line.startswith("#")
                    else md_file.stem
                )

                docs.append(
                    {
                        "file_path": str(md_file.relative_to(base_dir)),
                        "category": category,
                        "title": title,
                        "content": content[:3000],
                    }
                )
            except Exception as e:
                print(f"  警告: 读取 {md_file} 失败: {e}")

    return docs


def compute_embeddings(docs: list[dict[str, Any]], client: OpenAI) -> list[list[float]]:
    """计算文档的语义嵌入向量"""
    embeddings = []

    for i, doc in enumerate(docs):
        text = doc.get("title", "") + " " + doc.get("content", "")[:1000]

        if i % 5 == 0:
            print(f"  嵌入进度: {i}/{len(docs)}")

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


def cluster_docs(
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


def extract_triplets(client: OpenAI, docs_texts: list[dict[str, str]]) -> str:
    """使用 LLM 提取知识图谱三元组"""
    combined = "\n\n".join(
        [
            f"标题: {d['title']}\n分类: {d['category']}\n内容: {d['content'][:800]}"
            for d in docs_texts[:8]
        ]
    )

    prompt = f"""从以下知识库文档中提取知识图谱三元组。
要求：
1. 提取实体和它们之间的关系
2. 关系用动词或介词短语表示
3. 只提取核心知识，忽略描述性内容

文档内容：
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
    client: OpenAI, ttl_content: str, docs_titles: list[str]
) -> dict[str, Any]:
    """评估 TTL 知识图谱质量"""
    prompt = f"""请评估以下知识图谱的质量。

注意：此知识库用于探索性知识工程。
- 目标是发现模糊、建立关联、帮助探究
- 不应追求完整性、准确性、闭合答案
- 相反，应欣赏开放性关联、跨领域连接、启发性假设

知识图谱TTL内容：
{ttl_content}

相关文档标题：{docs_titles}

请从以下维度评估并输出JSON格式结果：
{{
    "novel_connections": 0-100,  // 新颖连接：是否发现了非常规的跨领域关联
    "provocativeness": 0-100,     // 启发性：是否能激发进一步探究和思考
    "fuzziness_tolerance": 0-100, // 模糊容忍：是否能接受不完整、不确定的关联
    "issues": ["问题1"],         // 发现的实际问题（语法错误等）
    "suggestions": ["建议1"]      // 改进建议
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


def summarize_content(client: OpenAI, docs: list[dict[str, Any]]) -> str:
    """使用 LLM 生成内容介绍"""
    sample_docs = docs[:10]
    combined = "\n\n".join(
        [
            f"标题: {d.get('title', '')}\n分类: {d.get('category', '')}\n内容: {d.get('content', '')[:500]}"
            for d in sample_docs
        ]
    )

    prompt = f"""请为以下知识库内容生成一个简洁的介绍（200字以内）。

知识库内容：
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
    client: OpenAI, docs: list[dict[str, Any]]
) -> dict[str, Any]:
    """评估知识库内容质量"""
    sample_docs = docs[:8]
    combined = "\n\n".join(
        [
            f"标题: {d.get('title', '')}\n分类: {d.get('category', '')}\n内容: {d.get('content', '')[:600]}"
            for d in sample_docs
        ]
    )

    prompt = f"""请评估以下知识库内容的质量。

注意：此知识库是智能体训练的原始素材，用于探索性的知识工程。
- 目标是发现模糊、帮助人类找到探究方式
- 相比于传统的知识工程（追求完整、准确、闭合），我们更欣赏探索性、开放性、启发性
- 不应以"缺乏完整性"、"缺乏准确性"、"缺乏标准分类"为由扣分
- 相反，应该鼓励模糊性、开放性问题、未完成的思考、多样视角

知识库内容：
{combined}

请从以下维度评估并输出JSON格式结果：
{{
    "exploratory": 0-100,   // 探索性：是否包含开放性问题、未完成的思考、启发性观点
    "curiosity": 0-100,     // 好奇心：是否能激发探究欲望，引发进一步思考
    "unconventional": 0-100, // 非传统性：是否跳出常规思维，有独特视角
    "inspiration": 0-100,   // 灵感激发：是否能给人带来灵感或新视角
    "issues": ["问题1"],    // 发现的实际问题（仅限真正影响智能体训练的问题）
    "suggestions": ["建议1"] // 改进建议（仅限有价值的建议）
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
    total_docs: int,
    clusters: list[dict[str, Any]],
    ttl_file: Path,
    quality_results: list[dict[str, Any]],
    output_dir: Path,
    docs: list[dict[str, Any]] | None = None,
    content_intro: str | None = None,
    content_quality: dict[str, Any] | None = None,
    similarity_threshold: float = 0.5,
    enable_quality_check: bool = True,
) -> dict[str, Any]:
    """生成分析报告"""
    avg_novel_connections = (
        sum(q.get("novel_connections", 0) for q in quality_results)
        / len(quality_results)
        if quality_results
        else 0
    )
    avg_provocativeness = (
        sum(q.get("provocativeness", 0) for q in quality_results) / len(quality_results)
        if quality_results
        else 0
    )
    avg_fuzziness_tolerance = (
        sum(q.get("fuzziness_tolerance", 0) for q in quality_results)
        / len(quality_results)
        if quality_results
        else 0
    )

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_docs": total_docs,
        "total_clusters": len(clusters),
    }

    md_report = [
        "# 知识库分析报告",
        "",
        f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **文档总数**: {total_docs}",
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
                f"## 分组 {cid}: {cluster['doc_count']} 篇文档",
                "",
                "**文档标题:**",
            ]
        )
        for item in cluster["titles"]:
            md_report.append(
                f"- [{item['title']}]({item['path']}) ({item['category']})"
            )
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
        "# 知识库分析评估",
        "",
        f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **文档总数**: {total_docs}",
        f"- **发现分组数**: {len(clusters)}",
        "",
    ]

    if content_quality and not content_quality.get("error"):
        md_eval.extend(
            [
                "## 内容质量评估",
                "",
                "此知识库用于探索性知识工程，目标是发现模糊、帮助人类找到探究方式。",
                "",
                f"| 维度 | 分数 |",
                f"| --- | --- |",
                f"| 探索性 (Exploratory) | {content_quality.get('exploratory', '-')} |",
                f"| 好奇心 (Curiosity) | {content_quality.get('curiosity', '-')} |",
                f"| 非传统性 (Unconventional) | {content_quality.get('unconventional', '-')} |",
                f"| 灵感激发 (Inspiration) | {content_quality.get('inspiration', '-')} |",
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
            "目标是发现模糊、建立关联、帮助探究。",
            "",
            f"| 维度 | 分数 |",
            f"| --- | --- |",
            f"| 新颖连接 (Novel Connections) | {avg_novel_connections:.1f} |",
            f"| 启发性 (Provocativeness) | {avg_provocativeness:.1f} |",
            f"| 模糊容忍 (Fuzziness Tolerance) | {avg_fuzziness_tolerance:.1f} |",
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
                    f"- 新颖连接: {quality.get('novel_connections', '-')}",
                    f"- 启发性: {quality.get('provocativeness', '-')}",
                    f"- 模糊容忍: {quality.get('fuzziness_tolerance', '-')}",
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
        "# 知识库分析复盘",
        "",
        f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **文档总数**: {total_docs}",
        f"- **发现分组数**: {len(clusters)}",
        "",
        "## 算法流程",
        "",
        "1. **文档扫描**: 扫描知识库目录，加载所有 Markdown 文件",
        "2. **语义嵌入**: 使用 OpenAI Embedding API 获取文本语义向量",
        "3. **相似度计算**: 使用余弦相似度计算文档之间的相似度",
        "4. **分组聚类**: 基于相似度阈值(0.5)进行聚类",
        "5. **知识抽取**: 使用 LLM 提取知识图谱三元组",
        "6. **质量评估**: 使用 LLM 评估知识图谱质量",
        "",
        "## 参数配置",
        "",
        f"- 相似度阈值: {similarity_threshold}",
        f"- 质量评估: {'启用' if enable_quality_check else '禁用'}",
        "",
    ]

    with open(output_dir / "复盘.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_review))

    return report


def run_profile_activity(
    data_dir: Path | None = None,
    output_dir: Path | None = None,
    similarity_threshold: float = 0.5,
    enable_quality_check: bool = True,
) -> dict[str, Any]:
    """运行知识发现活动

    Args:
        data_dir: 知识库数据目录
        output_dir: 输出目录
        similarity_threshold: 相似度阈值
        enable_quality_check: 是否启用质量评估
    """
    if data_dir is None:
        data_dir = (
            Path(__file__).parent.parent.parent.parent / "data" / "infra" / "github"
        )
    if output_dir is None:
        output_dir = (
            Path(__file__).parent.parent.parent.parent / "data" / "activity" / "profile"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    client = create_llm_client()

    print("扫描知识库...")
    docs = scan_knowledge_base(data_dir)
    print(f"加载了 {len(docs)} 篇文档")

    print("计算语义嵌入向量...")
    embeddings = compute_embeddings(docs, client)
    print(f"计算了 {len(embeddings)} 个嵌入向量")

    similarity_matrix = compute_similarity(embeddings)

    vector_data = {
        "docs": [
            {
                "index": i,
                "title": docs[i].get("title", ""),
                "category": docs[i].get("category", ""),
            }
            for i in range(len(docs))
        ],
        "embeddings": embeddings,
        "similarity_matrix": similarity_matrix,
    }
    vector_file = output_dir / "vectors.json"
    with open(vector_file, "w", encoding="utf-8") as f:
        json.dump(vector_data, f, ensure_ascii=False)
    print(f"向量数据已保存到: {vector_file}")

    clusters = cluster_docs(similarity_matrix, threshold=similarity_threshold)
    print(f"发现 {len(clusters)} 个分组")

    ttl_lines = [
        "@prefix kb: <http://example.org/knowledge/> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "",
    ]

    cluster_results = []
    quality_results = []

    for idx, cluster in enumerate(clusters):
        cluster_docs_list = [docs[i] for i in cluster]
        titles = [
            {
                "title": d.get("title", ""),
                "path": d.get("file_path", ""),
                "category": d.get("category", ""),
            }
            for d in cluster_docs_list
        ]

        print(f"  处理 Cluster {idx + 1} ({len(cluster)} docs)...")

        ttl_triplets = extract_triplets(client, cluster_docs_list)

        ttl_lines.append(f"# Cluster {idx + 1}: {len(cluster)} related docs")
        ttl_lines.append(ttl_triplets)
        ttl_lines.append("")

        quality = {}
        if enable_quality_check and ttl_triplets:
            print(f"    评估质量...")
            quality = evaluate_ttl_quality(
                client, ttl_triplets, [t["title"] for t in titles]
            )
            quality_results.append(
                {
                    "cluster_id": idx + 1,
                    **quality,
                }
            )

        cluster_results.append(
            {
                "cluster_id": idx + 1,
                "doc_count": len(cluster),
                "titles": titles,
                "keywords": _extract_keywords([t["title"] for t in titles]),
                "quality": quality,
            }
        )

    ttl_file = output_dir / "knowledge.ttl"
    with open(ttl_file, "w", encoding="utf-8") as f:
        f.write("\n".join(ttl_lines))
    print(f"知识图谱已保存到: {ttl_file}")

    print("生成内容介绍...")
    content_intro = summarize_content(client, docs)

    print("评估内容质量...")
    content_quality = {}
    if enable_quality_check:
        content_quality = evaluate_content_quality(client, docs)

    report = generate_report(
        len(docs),
        cluster_results,
        ttl_file,
        quality_results,
        output_dir,
        docs=docs,
        content_intro=content_intro,
        content_quality=content_quality,
        similarity_threshold=similarity_threshold,
        enable_quality_check=enable_quality_check,
    )
    print(f"分析报告已保存到: {output_dir / '报告.md'}")

    return report


def _extract_keywords(texts: list[str]) -> list[str]:
    """提取关键词"""
    all_text = " ".join(texts)
    words = re.findall(r"[\u4e00-\u9fa5]{2,4}", all_text)
    counter = Counter(words)
    return [w for w, _ in counter.most_common(15)]


if __name__ == "__main__":
    run_profile_activity()

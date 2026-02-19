"""
知识工程域 - 知识图谱、RAG、知识发现
"""

import json
import re
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

from thera.config import settings
from quanttide_agent import (
    chat_str as llm_chat_str,
    embedding_similarity_matrix,
    extract_keywords,
    extract_triplets,
    find_bridge_notes,
    find_cross_cluster_links,
    get_embedding,
    get_embeddings,
    json_request as llm_json_request,
    stream as llm_stream,
)


class DocType(Enum):
    OUTLINE = "提纲"
    DRAFT = "初稿"
    OTHER = "其他"


def classify_doc_type(file_path: Path) -> DocType:
    path_str = str(file_path)
    if "/提纲/" in path_str or path_str.endswith("/提纲.md"):
        return DocType.OUTLINE
    elif "/初稿/" in path_str or path_str.endswith("/初稿.md"):
        return DocType.DRAFT
    return DocType.OTHER


def load_articles(docs_dir: Path) -> tuple[dict[str, dict], dict]:
    articles = {}
    doc_types = {DocType.OUTLINE: [], DocType.DRAFT: [], DocType.OTHER: []}

    for f in sorted(docs_dir.glob("**/*.md")):
        if f.name.startswith("_") or f.name in [
            "feishu_wiki_directory.json",
            "feishu_wiki_directory.yaml",
        ]:
            continue
        content = f.read_text(encoding="utf-8")
        title = content.split("\n")[0].strip("# ").strip()
        doc_type = classify_doc_type(f)

        articles[f.stem] = {
            "title": title,
            "content": content,
            "doc_type": doc_type,
            "path": str(f.relative_to(docs_dir)),
        }
        doc_types[doc_type].append(f.stem)

    return articles, doc_types


def compute_all_similarities(articles: dict[str, dict]) -> dict:
    import numpy as np
    from quanttide_agent import (
        embedding_similarity,
        get_embeddings,
        jaccard_similarity,
        keyword_similarity,
        tfidf_similarity,
    )

    names = list(articles.keys())
    contents = [articles[n]["content"] for n in names]

    n = len(names)
    results = {
        "jaccard": np.zeros((n, n)),
        "keyword": np.zeros((n, n)),
    }

    for i in range(n):
        for j in range(n):
            if i == j:
                results["jaccard"][i][j] = 1.0
                results["keyword"][i][j] = 1.0
            else:
                results["jaccard"][i][j] = jaccard_similarity(contents[i], contents[j])
                results["keyword"][i][j] = keyword_similarity(contents[i], contents[j])

    tfidf_sim = tfidf_similarity(contents)
    results["tfidf"] = tfidf_sim

    embeddings = get_embeddings(contents)
    embedding_sim = embedding_similarity(np.array(embeddings))
    results["embedding"] = embedding_sim

    return {"names": names, "similarities": results}


def build_similarity_report(sim_results: dict) -> str:
    names = sim_results["names"]
    sims = sim_results["similarities"]

    report_lines = ["# 文本相似度分析报告\n", "## 1. 相似度矩阵\n"]

    for method in ["jaccard", "keyword", "tfidf", "embedding"]:
        if method in sims:
            sim_matrix = sims[method]
            report_lines.append(f"\n### {method}\n")
            header = "".join([f"{n:>12}" for n in names])
            report_lines.append(f"{'':>12}{header}")
            report_lines.append("-" * (12 * len(names) + 12))

            for i, name in enumerate(names):
                row = "".join([f"{sim_matrix[i][j]:>12.4f}" for j in range(len(names))])
                report_lines.append(f"{name:>12}{row}")

    report_lines.append("\n## 2. 方法说明\n")
    report_lines.append("- **Jaccard**: 基于3-gram字符集合的交集/并集")
    report_lines.append("- **Keyword**: 基于2+字符词的Jaccard相似度")
    report_lines.append("- **TF-IDF**: 基于TF-IDF向量的余弦相似度")
    report_lines.append("- **Embedding**: 基于LLM语义向量的余弦相似度")

    report_lines.append("\n## 3. 各方法Top相似对\n")
    for method in ["jaccard", "keyword", "tfidf", "embedding"]:
        if method not in sims:
            continue
        pairs = []
        n = len(names)
        for i in range(n):
            for j in range(i + 1, n):
                pairs.append((names[i], names[j], sims[method][i][j]))

        pairs.sort(key=lambda x: x[2], reverse=True)
        report_lines.append(f"\n### {method}")
        for a, b, score in pairs[:3]:
            report_lines.append(f"- {a} <-> {b}: {score:.4f}")

    return "\n".join(report_lines)


def discover_with_llm(
    articles: dict[str, dict], sim_results: dict, doc_types: dict
) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.llm_api_key, base_url=settings.llm_base_url, timeout=180.0
    )

    names = sim_results["names"]
    sims = sim_results["similarities"]

    outline_names = [n for n in names if articles[n]["doc_type"] == DocType.OUTLINE]
    draft_names = [n for n in names if articles[n]["doc_type"] == DocType.DRAFT]

    def get_sim_summary(name_list: list[str], sim_matrix: np.ndarray) -> str:
        if len(name_list) < 2:
            return "（文档数量不足）"

        name_to_idx = {n: i for i, n in enumerate(names)}
        pairs = []
        for i, a in enumerate(name_list):
            for b in name_list[i + 1 :]:
                a_idx = name_to_idx[a]
                b_idx = name_to_idx[b]
                pairs.append((a, b, sim_matrix[a_idx][b_idx]))

        pairs.sort(key=lambda x: x[2], reverse=True)
        return "\n".join(
            [
                f"  {rank}. {a} ↔ {b}: {s:.4f}"
                for rank, (a, b, s) in enumerate(pairs[:5], 1)
            ]
        )

    sim_summary = f"""
## 提纲类文档（{len(outline_names)} 篇）内部相似度排名
{get_sim_summary(outline_names, sims["embedding"])}

## 初稿类文档（{len(draft_names)} 篇）内部相似度排名
{get_sim_summary(draft_names, sims["embedding"])}

## 提纲与初稿跨类相似度排名
"""

    if outline_names and draft_names:
        name_to_idx = {n: i for i, n in enumerate(names)}
        cross_pairs = []
        for o in outline_names:
            for d in draft_names:
                o_idx = name_to_idx[o]
                d_idx = name_to_idx[d]
                cross_pairs.append((o, d, sims["embedding"][o_idx][d_idx]))

        cross_pairs.sort(key=lambda x: x[2], reverse=True)
        sim_summary += "\n".join(
            [
                f"  {rank}. 提纲:{a} ↔ 初稿:{b}: {s:.4f}"
                for rank, (a, b, s) in enumerate(cross_pairs[:10], 1)
            ]
        )

    outline_summaries = []
    draft_summaries = []
    other_summaries = []

    for name in names:
        info = articles[name]
        doc_type = info["doc_type"]
        content = info["content"]
        path = info.get("path", "")

        summary = f"### {info['title']}\n路径: {path}\n类型: {doc_type.value}\n\n{content[:800]}"

        if doc_type == DocType.OUTLINE:
            outline_summaries.append(summary)
        elif doc_type == DocType.DRAFT:
            draft_summaries.append(summary)
        else:
            other_summaries.append(summary)

    prompt = f"""你是一个专业的故事创作知识分析助手，擅长从提纲和初稿文本中发现知识关联。

## 背景
当前分析的文本分为两类：
- **提纲**：概念性、设定性内容，包含主题、人物、剧情、环境等设计文档
- **初稿**：叙事性、场景化内容，包含具体的故事情节、对话、描写等

## 任务
分析提纲与初稿之间的对应关系，发现创作中的知识关联和洞察。

## 相似度分析结果
{sim_summary}

## 提纲类文档
{chr(10).join(outline_summaries)}

## 初稿类文档
{chr(10).join(draft_summaries)}

## 要求
1. 区分分析提纲和初稿的各自特点
2. 找出提纲与初稿之间的对应关系
3. 发现提纲中的设定在初稿中是如何体现的
4. 分析创作过程中的知识转化和演变
5. 提炼对创作有帮助的洞察

请按以下格式输出：
## 知识发现报告

### 1. 文本分类概览
### 2. 提纲分析
### 3. 初稿分析
### 4. 提纲与初稿跨类相似度分析
### 5. 提纲与初稿对应关系
### 6. 创作洞察"""

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": "你是一个专业的故事创作知识分析助手，擅长分析提纲和初稿之间的关系。",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content or ""


def export_html(markdown_path: Path, html_path: Path):
    markdown_content = markdown_path.read_text(encoding="utf-8")

    markdown_content = markdown_content.replace("```mermaid", "<pre><code>").replace(
        "```", "</code></pre>"
    )
    markdown_content = markdown_content.replace("## ", "<h2>").replace("### ", "<h3>")
    markdown_content = markdown_content.replace("\n\n", "</p><p>")
    markdown_content = markdown_content.replace("- ", "<li>")
    markdown_content = markdown_content.replace("| ", "<tr><td>").replace("|", "</td>")

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>知识发现报告</title>
    <style>
        @page {{ size: A4; margin: 2cm; }}
        body {{
            font-family: "PingFang SC", "Microsoft YaHei", "SimSun", sans-serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{ font-size: 24pt; text-align: center; margin-bottom: 20pt; }}
        h2 {{ font-size: 18pt; margin-top: 25pt; color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 5pt; }}
        h3 {{ font-size: 14pt; margin-top: 15pt; color: #34495e; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10pt 0; }}
        th, td {{ border: 1px solid #ddd; padding: 6pt; text-align: left; font-size: 10pt; }}
        th {{ background-color: #f5f5f5; }}
        code {{ background-color: #f8f8f8; padding: 2pt 4pt; border-radius: 3pt; font-size: 10pt; }}
        pre {{ background-color: #f8f8f8; padding: 10pt; border-radius: 5pt; overflow-x: auto; font-size: 10pt; }}
        blockquote {{ border-left: 4pt solid #ddd; margin: 10pt 0; padding-left: 10pt; color: #666; }}
        ul, ol {{ margin: 5pt 0; padding-left: 20pt; }}
        li {{ margin: 3pt 0; }}
        img {{ max-width: 100%; }}
    </style>
</head>
<body>
<p>{markdown_content}</p>
</body>
</html>"""

    html_path.write_text(html_content, encoding="utf-8")


def cluster_notes(
    similarity_matrix: list[list[float]],
    threshold: float = 0.5,
) -> list[list[int]]:
    from quanttide_agent import cluster_notes as _cluster_notes

    return _cluster_notes(similarity_matrix, threshold)


def extract_keywords(texts: list[str], top_n: int = 15) -> list[str]:
    from quanttide_agent import extract_keywords as _extract_keywords

    return _extract_keywords(texts, top_n)


def generate_report(
    total_items: int,
    clusters: list[dict[str, Any]],
    ttl_file: Path,
    quality_results: list[dict[str, Any]],
    output_dir: Path,
    title: str = "分析报告",
    content_intro: str | None = None,
    content_quality: dict[str, Any] | None = None,
    quality_template: dict[str, tuple[str, str]] | None = None,
    item_label: str = "条目",
    cluster_label: str = "分组",
) -> dict[str, Any]:
    """通用报告生成"""
    import re
    from collections import Counter
    from datetime import datetime

    avg_quality = {}
    if quality_results and quality_template:
        for key in quality_template.keys():
            values = [q.get(key, 0) for q in quality_results if q.get(key)]
            if values:
                avg_quality[key] = sum(values) / len(values)

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_items": total_items,
        "total_clusters": len(clusters),
    }

    md_report = [
        f"# {title}",
        "",
        f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **条目总数**: {total_items}",
        f"- **发现分组数**: {len(clusters)}",
        "",
    ]

    if content_intro:
        md_report.extend(["## 内容介绍", "", content_intro, ""])

    for cluster in clusters:
        cid = cluster["cluster_id"]
        md_report.extend(
            [
                f"## {cluster_label} {cid}: {cluster.get('note_count', cluster.get('doc_count', len(cluster.get('indices', []))))} {item_label}",
                "",
                f"**标题:**",
            ]
        )
        for title_item in cluster.get("titles", [])[:10]:
            md_report.append(f"- {title_item}")
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
        f"# {title}评估",
        "",
        f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **条目总数**: {total_items}",
        f"- **发现分组数**: {len(clusters)}",
        "",
    ]

    if content_quality and not content_quality.get("error") and quality_template:
        md_eval.extend(["## 内容质量评估", ""])
        md_eval.append(f"| 维度 | 分数 |")
        md_eval.append(f"| --- | --- |")
        for key, (label, _) in quality_template.items():
            md_eval.append(f"| {label} | {content_quality.get(key, '-')} |")
        md_eval.append("")

    if quality_template:
        md_eval.extend(["## 知识图谱质量评估", ""])
        md_eval.append(f"| 维度 | 分数 |")
        md_eval.append(f"| --- | --- |")
        for key, (label, _) in quality_template.items():
            val = avg_quality.get(key)
            if isinstance(val, (int, float)):
                md_eval.append(f"| {label} | {val:.1f} |")
            else:
                md_eval.append(f"| {label} | - |")
        md_eval.append("")

    with open(output_dir / "评估.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_eval))

    return report


def compute_cluster_centroids(
    embeddings: list[list[float]], clusters: list[list[int]]
) -> list[list[float]]:
    from quanttide_agent import compute_cluster_centroids as _compute_cluster_centroids

    return _compute_cluster_centroids(embeddings, clusters)


def find_bridge_notes(
    embeddings: list[list[float]], clusters: list[list[int]], threshold: float = 0.3
) -> list[dict[str, Any]]:
    from quanttide_agent import find_bridge_notes as _find_bridge_notes

    return _find_bridge_notes(embeddings, clusters, threshold)


def find_cross_cluster_links(
    embeddings: list[list[float]], clusters: list[list[int]], top_n: int = 3
) -> list[dict[str, Any]]:
    from quanttide_agent import find_cross_cluster_links as _find_cross_cluster_links

    return _find_cross_cluster_links(embeddings, clusters, top_n)


def generate_reasoning_report(
    direction_analysis: dict[str, Any],
    clusters: list[dict[str, Any]],
    output_dir: Path,
    title: str = "推理报告",
) -> str:
    """生成推理报告"""
    from datetime import datetime

    md = [
        f"# {title}",
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

    report_path = output_dir / f"{title}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    return str(report_path)

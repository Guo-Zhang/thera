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
from pathlib import Path
from typing import Any

from quanttide_agent import (
    evaluate_content_quality as llm_evaluate_content,
    evaluate_ttl_quality as llm_evaluate_ttl,
    extract_triplets as llm_extract_triplets,
    summarize_content as llm_summarize_content,
)
from thera.mode.knowl import (
    cluster_notes,
    embedding_similarity_matrix,
    extract_keywords,
    generate_report,
    get_embeddings,
)


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


def run_profile_activity(
    data_dir: Path | None = None,
    output_dir: Path | None = None,
    similarity_threshold: float = 0.5,
    enable_quality_check: bool = True,
) -> dict[str, Any]:
    """运行知识发现活动"""
    if data_dir is None:
        data_dir = (
            Path(__file__).parent.parent.parent.parent / "data" / "infra" / "github"
        )
    if output_dir is None:
        output_dir = (
            Path(__file__).parent.parent.parent.parent / "data" / "activity" / "profile"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    print("扫描知识库...")
    docs = scan_knowledge_base(data_dir)
    print(f"加载了 {len(docs)} 篇文档")

    print("计算语义嵌入向量...")
    texts = [d.get("title", "") + " " + d.get("content", "")[:1000] for d in docs]
    embeddings = get_embeddings(texts)
    print(f"计算了 {len(embeddings)} 个嵌入向量")

    similarity_matrix = embedding_similarity_matrix(embeddings).tolist()

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

    clusters_indices = cluster_notes(similarity_matrix, similarity_threshold)
    print(f"发现 {len(clusters_indices)} 个分组")

    ttl_lines = [
        "@prefix kb: <http://example.org/knowledge/> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "",
    ]

    cluster_results = []
    quality_results = []

    for idx, cluster in enumerate(clusters_indices):
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

        ttl = llm_extract_triplets(
            cluster_docs_list,
            lambda d: f"标题: {d.get('title', '')}\n分类: {d.get('category', '')}\n内容: {d.get('content', '')[:800]}",
            max_items=8,
            max_content=800,
        )

        ttl_lines.append(f"# Cluster {idx + 1}: {len(cluster)} related docs")
        ttl_lines.append(ttl)
        ttl_lines.append("")

        quality = {}
        if enable_quality_check and ttl:
            print(f"    评估质量...")
            quality = llm_evaluate_ttl(
                ttl,
                [t["title"] for t in titles],
                {
                    "novel_connections": "新颖连接：是否发现了非常规的跨领域关联",
                    "provocativeness": "启发性：是否能激发进一步探究和思考",
                    "fuzziness_tolerance": "模糊容忍：是否能接受不完整、不确定的关联",
                    "issues": "发现的问题",
                    "suggestions": "改进建议",
                },
                context="注意：此知识库用于探索性知识工程。目标是发现模糊、建立关联、帮助探究。",
            )
            quality_results.append({"cluster_id": idx + 1, **quality})

        cluster_results.append(
            {
                "cluster_id": idx + 1,
                "doc_count": len(cluster),
                "titles": titles,
                "keywords": extract_keywords([t["title"] for t in titles]),
                "quality": quality,
            }
        )

    ttl_file = output_dir / "knowledge.ttl"
    with open(ttl_file, "w", encoding="utf-8") as f:
        f.write("\n".join(ttl_lines))
    print(f"知识图谱已保存到: {ttl_file}")

    print("生成内容介绍...")
    content_intro = llm_summarize_content(
        docs,
        lambda d: f"标题: {d.get('title', '')}\n分类: {d.get('category', '')}\n内容: {d.get('content', '')[:500]}",
        max_items=10,
        max_content=500,
        max_length=200,
    )

    print("评估内容质量...")
    content_quality = {}
    if enable_quality_check:
        content_quality = llm_evaluate_content(
            docs,
            lambda d: f"标题: {d.get('title', '')}\n分类: {d.get('category', '')}\n内容: {d.get('content', '')[:600]}",
            {
                "exploratory": "探索性：是否包含开放性问题、未完成的思考、启发性观点",
                "curiosity": "好奇心：是否能激发探究欲望，引发进一步思考",
                "unconventional": "非传统性：是否跳出常规思维，有独特视角",
                "inspiration": "灵感激发：是否能给人带来灵感或新视角",
                "issues": "发现的问题",
                "suggestions": "改进建议",
            },
            max_items=8,
            max_content=600,
        )

    quality_template = {
        "novel_connections": ("新颖连接", "novel_connections"),
        "provocativeness": ("启发性", "provocativeness"),
        "fuzziness_tolerance": ("模糊容忍", "fuzziness_tolerance"),
    }

    report = generate_report(
        total_items=len(docs),
        clusters=cluster_results,
        ttl_file=ttl_file,
        quality_results=quality_results,
        output_dir=output_dir,
        title="知识库分析报告",
        content_intro=content_intro,
        content_quality=content_quality,
        quality_template=quality_template,
        item_label="篇文档",
        cluster_label="分组",
    )

    with open(output_dir / "复盘.md", "w", encoding="utf-8") as f:
        f.write(f"""# 知识库分析复盘

- **生成时间**: {report["generated_at"]}
- **文档总数**: {len(docs)}
- **发现分组数**: {len(clusters_indices)}

## 算法流程

1. **文档扫描**: 扫描知识库目录，加载所有 Markdown 文件
2. **语义嵌入**: 使用 OpenAI Embedding API 获取文本语义向量
3. **相似度计算**: 使用余弦相似度计算文档之间的相似度
4. **分组聚类**: 基于相似度阈值({similarity_threshold})进行聚类
5. **知识抽取**: 使用 LLM 提取知识图谱三元组
6. **质量评估**: 使用 LLM 评估知识图谱质量

## 参数配置

- 相似度阈值: {similarity_threshold}
- 质量评估: {"启用" if enable_quality_check else "禁用"}
""")

    print(f"分析报告已保存到: {output_dir / '报告.md'}")

    return report


if __name__ == "__main__":
    run_profile_activity()

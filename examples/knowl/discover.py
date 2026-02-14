"""
目标：从人工挑选个别文章到自主发现新知识。
输入：
- 路径：项目根目录 `data/docs/fiction`
- 内容：从近期文章中选取代表性文本作为原始素材。
- 格式：知识是文本格式，文本长度约 1000字左右。
- 内容：
    1. 不同维度的文本相似度。
    2. 基于文本相似度的知识发现结果。
- 路径：项目根目录 `data/knowl`
算法：
1. 不同方法计算文本相似度。
2. 使用 Kimi或者智谱解析得到知识发现报告。
3. 自动识别和分类提纲与初稿文本。
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from enum import Enum

import numpy as np
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.thera.config import settings

DOCS_DIR = Path("data/docs/fiction")
KNOWL_DIR = Path("data/knowl")


class DocType(Enum):
    OUTLINE = "提纲"  # 提纲类
    DRAFT = "初稿"  # 初稿类
    OTHER = "其他"


def classify_doc_type(file_path: Path) -> DocType:
    """根据文件路径自动识别文档类型（提纲/初稿）"""
    path_str = str(file_path)

    if "/提纲/" in path_str or path_str.endswith("/提纲.md"):
        return DocType.OUTLINE
    elif "/初稿/" in path_str or path_str.endswith("/初稿.md"):
        return DocType.DRAFT
    else:
        return DocType.OTHER


def load_articles(docs_dir: Path = DOCS_DIR) -> tuple[dict[str, dict], dict]:
    """加载 docs/fiction 目录下的所有文章，并自动分类"""
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


def get_embeddings(texts: list[str], batch_size: int = 10) -> np.ndarray:
    """使用 LLM 获取文本 embedding，分批处理"""
    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)

    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(
            model=settings.llm_embedding_model, input=batch
        )
        all_embeddings.extend([d.embedding for d in response.data])

    return np.array(all_embeddings)


def embedding_similarity(embeddings: np.ndarray) -> np.ndarray:
    """基于 embedding 的余弦相似度"""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / (norms + 1e-8)
    return np.dot(normalized, normalized.T)


def jaccard_similarity(text1: str, text2: str) -> float:
    """Jaccard 相似度：基于字符 n-gram"""

    def get_ngrams(text: str, n: int = 3) -> set:
        text = re.sub(r"\s+", "", text.lower())
        return set(text[i : i + n] for i in range(len(text) - n + 1))

    ngrams1 = get_ngrams(text1)
    ngrams2 = get_ngrams(text2)

    if not ngrams1 or not ngrams2:
        return 0.0

    intersection = len(ngrams1 & ngrams2)
    union = len(ngrams1 | ngrams2)
    return intersection / union if union > 0 else 0.0


def tfidf_similarity(texts: list[str]) -> np.ndarray:
    """TF-IDF 余弦相似度"""
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4), max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(texts)
    return cosine_similarity(tfidf_matrix)


def keyword_similarity(text1: str, text2: str) -> float:
    """关键词相似度：基于词级别的 Jaccard"""

    def extract_keywords(text: str) -> set:
        text = re.sub(r"[^\w\u4e00-\u9fff]", " ", text)
        words = text.split()
        return set(w for w in words if len(w) >= 2)

    kw1 = extract_keywords(text1)
    kw2 = extract_keywords(text2)

    if not kw1 or not kw2:
        return 0.0

    intersection = len(kw1 & kw2)
    union = len(kw1 | kw2)
    return intersection / union


def compute_all_similarities(articles: dict[str, dict]) -> dict:
    """计算所有文章对的不同维度相似度"""
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

    print("正在计算 Embedding 语义相似度...")
    embeddings = get_embeddings(contents)
    embedding_sim = embedding_similarity(embeddings)
    results["embedding"] = embedding_sim

    return {"names": names, "similarities": results}


def format_similarity_matrix(
    names: list[str], sim_matrix: np.ndarray, method: str
) -> str:
    """格式化相似度矩阵为可读字符串"""
    lines = [f"\n### {method}\n"]
    header = "".join([f"{n:>12}" for n in names])
    lines.append(f"{'':>12}{header}")
    lines.append("-" * (12 * len(names) + 12))

    for i, name in enumerate(names):
        row = "".join([f"{sim_matrix[i][j]:>12.4f}" for j in range(len(names))])
        lines.append(f"{name:>12}{row}")

    return "\n".join(lines)


def build_similarity_report(sim_results: dict) -> str:
    """生成相似度分析报告"""
    names = sim_results["names"]
    sims = sim_results["similarities"]

    report_lines = ["# 文本相似度分析报告\n"]
    report_lines.append("## 1. 相似度矩阵\n")

    for method in ["jaccard", "keyword", "tfidf", "embedding"]:
        if method in sims:
            report_lines.append(format_similarity_matrix(names, sims[method], method))

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
    """使用 LLM 进行知识发现 - 基于相似度矩阵，自动区分提纲和初稿"""
    client = OpenAI(
        api_key=settings.llm_api_key, base_url=settings.llm_base_url, timeout=180.0
    )

    names = sim_results["names"]
    sims = sim_results["similarities"]

    outline_names = [n for n in names if articles[n]["doc_type"] == DocType.OUTLINE]
    draft_names = [n for n in names if articles[n]["doc_type"] == DocType.DRAFT]

    def get_sim_summary(name_list: list[str], sim_matrix: np.ndarray) -> str:
        """获取某类文档的相似度排名"""
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
2. 找出提纲与初稿之间的对应关系（如：哪篇初稿对应哪个提纲设定）
3. 发现提纲中的设定在初稿中是如何体现的
4. 分析创作过程中的知识转化和演变
5. 提炼对创作有帮助的洞察

请按以下格式输出：
## 知识发现报告

### 1. 文本分类概览
- 提纲数量及核心主题
- 初稿数量及主要场景
- 两类文本的总体特点

### 2. 提纲分析
- 各提纲的核心设定
- 提纲之间的关联

### 3. 初稿分析
- 各初稿的核心内容
- 初稿之间的关联

### 4. 提纲与初稿跨类相似度分析
基于 embedding 语义相似度，展示提纲与初稿之间的对应关系：
- 列出相似度最高的前10对提纲-初稿组合
- 分析这些高相似度组合的内在逻辑

### 5. 提纲与初稿对应关系
- 哪些初稿体现了哪些提纲设定
- 设定在叙事中的具体体现

### 6. 创作洞察
- 从提纲到初稿的转化过程
- 有价值的创作经验"""

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": "你是一个专业的故事创作知识分析助手，擅长分析提纲（设定/概念）和初稿（叙事/场景）之间的关系。",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    llm_content = response.choices[0].message.content

    return llm_content


def export_html(markdown_path: Path, html_path: Path):
    """将 Markdown 转换为可打印的 HTML"""
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
    print(f"HTML 已导出至: {html_path}")
    print("提示: 在浏览器中打开 HTML 文件，使用 Cmd+P 打印为 PDF")


def main():
    KNOWL_DIR.mkdir(parents=True, exist_ok=True)

    print("正在加载文章...")
    articles, doc_types = load_articles()
    print(f"已加载 {len(articles)} 篇文章")
    print(f"  - 提纲: {len(doc_types[DocType.OUTLINE])} 篇")
    print(f"  - 初稿: {len(doc_types[DocType.DRAFT])} 篇")
    print(f"  - 其他: {len(doc_types[DocType.OTHER])} 篇")

    print("正在计算文本相似度...")
    sim_results = compute_all_similarities(articles)

    sim_report_path = KNOWL_DIR / "similarity_report.md"
    sim_report = build_similarity_report(sim_results)
    sim_report_path.write_text(sim_report, encoding="utf-8")
    print(f"相似度报告已保存至: {sim_report_path}")

    print("正在进行知识发现分析...")
    full_report = discover_with_llm(articles, sim_results, doc_types)

    report_path = KNOWL_DIR / "knowledge_discovery.md"
    report_path.write_text(full_report, encoding="utf-8")
    print(f"知识发现报告已保存至: {report_path}")

    pdf_path = KNOWL_DIR / "knowledge_discovery.html"
    export_html(report_path, pdf_path)

    sim_json_path = KNOWL_DIR / "similarity_data.json"
    json_data = {
        "names": sim_results["names"],
        "similarities": {
            k: v.tolist() if isinstance(v, np.ndarray) else v.tolist()
            for k, v in sim_results["similarities"].items()
        },
    }
    sim_json_path.write_text(
        json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"相似度数据已保存至: {sim_json_path}")


if __name__ == "__main__":
    main()

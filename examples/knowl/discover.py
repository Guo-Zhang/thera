"""
目标：从人工挑选个别文章到自主发现新知识。
输入：
- 路径：项目根目录 `data/docs`的 article1-5
- 内容：从近期文章中选取和公司相关的 3-5 篇文本作为原始素材。
- 格式：知识是文本格式，文本长度约 1000-2000 字左右，即 iGuo 说公众号文本长度。暂不处理多模态、对话级短文本或者书籍级超长文本、专注于文章级文本。
输出：
- 内容：
    1. 不同维度的文本相似度。
    2. 基于文本相似度的知识发现结果。
- 路径：项目根目录 `data/knowl`
算法：
1. 不同方法计算文本相似度。
2. 使用 Kimi或者智谱解析得到知识发现报告。
"""

import json
import re
from pathlib import Path
from collections import defaultdict

from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from examples.knowl.config import settings


DOCS_DIR = Path("data/docs")
KNOWL_DIR = Path("data/knowl")


def load_articles(docs_dir: Path = DOCS_DIR) -> dict[str, dict]:
    """加载 docs 目录下的所有文章"""
    articles = {}
    for f in sorted(docs_dir.glob("article*.md")):
        content = f.read_text(encoding="utf-8")
        title = content.split("\n")[0].strip("# ").strip()
        articles[f.stem] = {"title": title, "content": content}
    return articles


def get_embeddings(texts: list[str]) -> np.ndarray:
    """使用 LLM 获取文本 embedding"""
    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)

    response = client.embeddings.create(model=settings.llm_embedding_model, input=texts)

    embeddings = np.array([d.embedding for d in response.data])
    return embeddings


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


def discover_with_llm(articles: dict[str, dict], sim_results: dict) -> str:
    """使用 LLM 进行知识发现 - 基于相似度矩阵"""
    client = OpenAI(
        api_key=settings.llm_api_key, base_url=settings.llm_base_url, timeout=180.0
    )

    names = sim_results["names"]
    sims = sim_results["similarities"]

    sim_summary_lines = []
    for method in ["embedding", "tfidf", "keyword", "jaccard"]:
        if method not in sims:
            continue
        pairs = []
        n = len(names)
        for i in range(n):
            for j in range(i + 1, n):
                pairs.append((names[i], names[j], sims[method][i][j]))
        pairs.sort(key=lambda x: x[2], reverse=True)

        sim_summary_lines.append(f"\n### {method.upper()} 相似度排名")
        for rank, (a, b, score) in enumerate(pairs, 1):
            sim_summary_lines.append(f"  {rank}. {a} ↔ {b}: {score:.4f}")

    sim_summary = "\n".join(sim_summary_lines)

    article_summaries = []
    for name in names:
        content = articles[name]["content"]
        article_summaries.append(f"## {name}\n{content[:1200]}")

    prompt = f"""你是一个专业的知识分析助手，擅长从多篇文章中发现知识关联。

## 任务
基于以下文章的相似度分析结果，发现知识关联和洞察。

## 相似度分析结果
{sim_summary}

## 文章内容
{chr(10).join(article_summaries)}

## 要求
1. 重点基于 **Embedding 语义相似度** 来分析文章间的知识关联（因为它代表语义层面的相似性）
2. 结合 TF-IDF、关键词、字符级相似度做交叉验证
3. 分析高相似度文章对之间的共同主题和差异
4. 发现潜在的新知识（跨文章洞察）
5. 提取对公司业务有价值的洞察

请按以下格式输出：
## 知识发现报告

### 1. 相似度分析解读
分析各方法的相似度结果，解释为什么某些文章对相似度高/低

### 2. 核心主题提炼
每篇文章的核心主题是什么

### 3. 知识关联图谱
基于相似度构建文章间的知识关联

### 4. 新知识发现
跨文章分析得出的新洞察

### 5. 业务价值洞察
对公司有价值的发现"""

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": "你是一个专业的知识分析助手，擅长从文本相似度分析中发现深层次的知识关联。",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    llm_content = response.choices[0].message.content

    full_report = "# 知识发现完整报告\n\n"
    full_report += build_similarity_report(sim_results)
    full_report += "\n\n---\n\n"
    full_report += llm_content

    return full_report


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
    articles = load_articles()
    print(f"已加载 {len(articles)} 篇文章")

    print("正在计算文本相似度...")
    sim_results = compute_all_similarities(articles)

    sim_report_path = KNOWL_DIR / "similarity_report.md"
    sim_report = build_similarity_report(sim_results)
    sim_report_path.write_text(sim_report, encoding="utf-8")
    print(f"相似度报告已保存至: {sim_report_path}")

    print("正在进行知识发现分析...")
    full_report = discover_with_llm(articles, sim_results)

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

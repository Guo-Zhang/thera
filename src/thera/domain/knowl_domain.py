"""
知识工程域 - 知识图谱、RAG、知识发现
"""

import json
import re
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from thera.meta import Mode, ModeType
from thera.config import settings


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


def get_embeddings(texts: list[str], batch_size: int = 10) -> np.ndarray:
    from openai import OpenAI

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
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / (norms + 1e-8)
    return np.dot(normalized, normalized.T)


def jaccard_similarity(text1: str, text2: str) -> float:
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
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4), max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(texts)
    return cosine_similarity(tfidf_matrix)


def keyword_similarity(text1: str, text2: str) -> float:
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
    embedding_sim = embedding_similarity(embeddings)
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

    return response.choices[0].message.content


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


class KnowlDomain(Mode):
    name = "knowl"
    description = "知识工程域 - 知识图谱、RAG"

    def __init__(self, app):
        super().__init__(app)
        self.articles = {}
        self.sim_results = {}

    def on_activate(self):
        print(f"Activated: {self.name}")

    def on_deactivate(self):
        print(f"Deactivated: {self.name}")

    def handle_input(self, user_input: str) -> str:
        if user_input.startswith("/discover"):
            return self._run_discovery()
        return f"[Knowl] {user_input}"

    def _run_discovery(self) -> str:
        docs_dir = self.app.storage.base_path / "docs" / "fiction"
        knowl_dir = self.app.storage.base_path / "knowl"

        if not docs_dir.exists():
            return f"Directory not found: {docs_dir}"

        knowl_dir.mkdir(parents=True, exist_ok=True)

        articles, doc_types = load_articles(docs_dir)
        if not articles:
            return f"No articles found in {docs_dir}"

        self.sim_results = compute_all_similarities(articles)

        sim_report = build_similarity_report(self.sim_results)
        (knowl_dir / "similarity_report.md").write_text(sim_report, encoding="utf-8")

        full_report = discover_with_llm(articles, self.sim_results, doc_types)
        (knowl_dir / "knowledge_discovery.md").write_text(full_report, encoding="utf-8")

        export_html(
            knowl_dir / "knowledge_discovery.md", knowl_dir / "knowledge_discovery.html"
        )

        sim_json = {
            "names": self.sim_results["names"],
            "similarities": {
                k: v.tolist() if isinstance(v, np.ndarray) else v
                for k, v in self.sim_results["similarities"].items()
            },
        }
        (knowl_dir / "similarity_data.json").write_text(
            json.dumps(sim_json, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        return f"Knowledge discovery completed. Reports saved to {knowl_dir}"

    def auto_switch(self, user_input: str) -> ModeType | None:
        if user_input.startswith("/think"):
            return ModeType.THINK
        if user_input.startswith("/write"):
            return ModeType.WRITE
        if user_input.startswith("/chat"):
            return ModeType.CHAT
        return None

"""
头脑风暴器

数据：
- 知识库：data/knowl/
- 小说简报：data/write/summary/fiction

目标：根据知识库的信息启发小说简报产生写作灵感。

算法：
1. 分析当前写作片段：
   - 从 fragment_analysis_report.yaml 提取片段特征（关键词、情感基调、最佳匹配）

2. 在知识库中找相关：
   - 用相似度匹配，找出当前片段最接近知识库中的哪个提纲/初稿
   - 利用已有的"提纲-初稿对应关系"模板

3. 建议下一步：
   - 知识库中哪些相关设定还未在当前小说中实现？
   - 基于已有对应关系，下一个自然的写作方向是什么？
"""

import json
import yaml
from pathlib import Path
from enum import Enum

import numpy as np
from openai import OpenAI

from src.thera.config import settings

KNOWL_DIR = Path("data/knowl")
WRITE_DIR = Path("data/write/summary/fiction")
OUTPUT_DIR = Path("data/think/brainstorming")


class DocType(Enum):
    OUTLINE = "提纲"
    DRAFT = "初稿"
    OTHER = "其他"


def classify_doc_type(file_path: Path) -> DocType:
    """根据文件路径自动识别文档类型"""
    path_str = str(file_path)
    if "/提纲/" in path_str or path_str.endswith("/提纲.md"):
        return DocType.OUTLINE
    elif "/初稿/" in path_str or path_str.endswith("/初稿.md"):
        return DocType.DRAFT
    else:
        return DocType.OTHER


def load_knowledge_base():
    """加载知识库数据"""
    print("加载知识库...")

    # 加载相似度数据
    sim_data_path = KNOWL_DIR / "similarity_data.json"
    if sim_data_path.exists():
        with open(sim_data_path, "r", encoding="utf-8") as f:
            similarity_data = json.load(f)
    else:
        similarity_data = None

    # 加载知识发现报告
    report_path = KNOWL_DIR / "knowledge_discovery.md"
    if report_path.exists():
        report_content = report_path.read_text(encoding="utf-8")
    else:
        report_content = ""

    # 加载原始 fiction 文档
    fiction_dir = Path("data/docs/fiction")
    fiction_docs = {}
    for f in fiction_dir.glob("**/*.md"):
        if f.name.startswith("_") or f.name in [
            "feishu_wiki_directory.json",
            "feishu_wiki_directory.yaml",
        ]:
            continue
        content = f.read_text(encoding="utf-8")
        title = content.split("\n")[0].strip("# ").strip()
        doc_type = classify_doc_type(f)
        fiction_docs[f.stem] = {
            "title": title,
            "content": content,
            "doc_type": doc_type,
            "path": str(f.relative_to(fiction_dir)),
        }

    print(f"  - 加载了 {len(fiction_docs)} 篇文档")
    print(
        f"  - 提纲: {sum(1 for d in fiction_docs.values() if d['doc_type'] == DocType.OUTLINE)} 篇"
    )
    print(
        f"  - 初稿: {sum(1 for d in fiction_docs.values() if d['doc_type'] == DocType.DRAFT)} 篇"
    )

    return {
        "similarity_data": similarity_data,
        "report": report_content,
        "fiction_docs": fiction_docs,
    }


def load_novel_summary():
    """加载小说简报数据"""
    print("加载小说简报...")

    # 加载片段分析报告
    report_path = WRITE_DIR / "fragment_analysis_report.yaml"
    with open(report_path, "r", encoding="utf-8") as f:
        fragment_data = yaml.safe_load(f)

    # 加载辅助内容
    aux_path = WRITE_DIR / "auxiliary_content.md"
    if aux_path.exists():
        aux_content = aux_path.read_text(encoding="utf-8")
    else:
        aux_content = ""

    fragments = fragment_data.get("fragment_analysis", [])
    print(f"  - 加载了 {len(fragments)} 个写作片段")

    return {
        "fragments": fragments,
        "auxiliary_content": aux_content,
        "summary": fragment_data.get("summary", {}),
    }


def compute_similarity(
    text: str, docs: dict[str, dict], batch_size: int = 10
) -> list[tuple[str, float]]:
    """计算文本与知识库文档的相似度"""
    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)

    # 获取查询文本的 embedding
    response = client.embeddings.create(
        model=settings.llm_embedding_model, input=[text]
    )
    query_embedding = np.array(response.data[0].embedding)

    # 简化处理：只计算与部分文档的相似度
    doc_names = list(docs.keys())[:20]
    doc_contents = [docs[n]["content"][:2000] for n in doc_names]

    # 批量获取 embedding
    all_embeddings = []
    for i in range(0, len(doc_contents), batch_size):
        batch = doc_contents[i : i + batch_size]
        response = client.embeddings.create(
            model=settings.llm_embedding_model, input=batch
        )
        all_embeddings.extend([d.embedding for d in response.data])

    results = []
    for i, name in enumerate(doc_names):
        doc_embedding = np.array(all_embeddings[i])

        # 余弦相似度
        sim = np.dot(query_embedding, doc_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding) + 1e-8
        )
        results.append((name, float(sim)))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def analyze_fragment(fragment: dict, knowl_data: dict) -> dict:
    """分析单个写作片段，找出知识库中的相关内容"""
    title = fragment.get("title", "")
    keywords = fragment.get("keywords", [])
    locations = fragment.get("locations", [])
    emotional_tone = fragment.get("emotional_tone", {})
    best_matches = fragment.get("best_matches", [])

    # 构造片段特征文本
    fragment_text = f"""
标题: {title}
关键词: {", ".join(keywords)}
场景: {", ".join(locations) if locations else "无"}
情感基调: {emotional_tone}
最佳匹配: {[m["title"] for m in best_matches[:3]]}
"""

    # 在知识库中找相关文档
    docs = knowl_data["fiction_docs"]
    related_docs = compute_similarity(
        fragment.get("title", "") + " " + " ".join(keywords[:5]), docs
    )

    # 筛选相关文档
    outline_related = []
    draft_related = []
    for doc_name, sim in related_docs:
        doc = docs[doc_name]
        if doc["doc_type"] == DocType.OUTLINE:
            outline_related.append((doc_name, sim, doc["title"]))
        elif doc["doc_type"] == DocType.DRAFT:
            draft_related.append((doc_name, sim, doc["title"]))

    return {
        "title": title,
        "keywords": keywords,
        "locations": locations,
        "emotional_tone": emotional_tone,
        "best_matches": best_matches,
        "outline_related": outline_related[:5],
        "draft_related": draft_related[:5],
    }


def find_gaps(analysis_results: list[dict], knowl_data: dict) -> list[dict]:
    """分析知识库中哪些设定还未被当前小说覆盖"""
    docs = knowl_data["fiction_docs"]

    # 统计已被覆盖的提纲
    covered_outlines = set()
    for result in analysis_results:
        for doc_name, _, _ in result.get("outline_related", []):
            covered_outlines.add(doc_name)

    # 找出未被覆盖的提纲
    uncovered = []
    for doc_name, doc in docs.items():
        if doc["doc_type"] == DocType.OUTLINE and doc_name not in covered_outlines:
            uncovered.append(
                {
                    "doc_name": doc_name,
                    "title": doc["title"],
                    "content": doc["content"][:500],
                }
            )

    return uncovered[:10]


def generate_hints(analysis_results: list[dict], knowl_data: dict) -> list[dict]:
    """基于知识库生成写作灵感建议"""
    docs = knowl_data["fiction_docs"]

    hints = []

    for result in analysis_results:
        title = result["title"]

        # 获取最相关的提纲
        related_outlines = result.get("outline_related", [])

        # 获取最相关的初稿
        related_drafts = result.get("draft_related", [])

        if related_outlines:
            # 基于提纲设定生成建议
            outline_name, _, outline_title = related_outlines[0]
            outline_content = docs[outline_name]["content"][:800]

            hints.append(
                {
                    "fragment": title,
                    "type": "outline_based",
                    "related_title": outline_title,
                    "suggestion": f"当前片段 '{title}' 与提纲 '{outline_title}' 相关。\n\n提纲设定：\n{outline_content}\n\n建议：可以将提纲中的设定进一步落地到当前片段中。",
                }
            )

        if related_drafts:
            # 基于相似初稿生成建议
            draft_name, _, draft_title = related_drafts[0]
            draft_content = docs[draft_name]["content"][:800]

            hints.append(
                {
                    "fragment": title,
                    "type": "draft_based",
                    "related_title": draft_title,
                    "suggestion": f"当前片段 '{title}' 与初稿 '{draft_title}' 风格相似。\n\n初稿参考：\n{draft_content[:500]}...\n\n建议：可以参考该初稿的叙事节奏和情感表达方式。",
                }
            )

    return hints


def suggest_with_llm(
    analysis_results: list[dict], knowl_data: dict, novel_data: dict
) -> str:
    """使用 LLM 生成深度写作建议"""
    client = OpenAI(
        api_key=settings.llm_api_key, base_url=settings.llm_base_url, timeout=180.0
    )

    # 构建上下文
    fragments_info = []
    for result in analysis_results[:5]:
        info = f"""
### {result["title"]}
- 关键词: {result["keywords"][:5]}
- 场景: {result["locations"] if result["locations"] else "无"}
- 相关提纲: {[t[2] for t in result["outline_related"][:3]]}
- 相关初稿: {[t[2] for t in result["draft_related"][:3]]}
"""
        fragments_info.append(info)

    # 知识库洞察摘要
    knowl_report = knowl_data["report"][:3000] if knowl_data["report"] else ""

    prompt = f"""我正在写一本现代都市情感小说，风格追求"东方古典式的克制"与"现代戏剧张力"的结合（类似《红楼梦》的内核重塑）。

请根据附件中的片段和提纲，进行针对性的写作指导。

## 当前写作片段分析
{"".join(fragments_info)}

## 知识库洞察（提纲与初稿的对应关系）
{knowl_report}

## 重要要求

### 拒绝学术黑话
禁止使用心理学、系统论、物理学等学术术语（如"熵增"、"认知校准"、"具身化"、"范式"等）。请使用文学语言，关注人物的潜意识、感官细节、环境氛围与情感张力。输出的建议必须具有可读性和画面感，而非分析报告。

### 聚焦核心氛围
我需要的是一种"此时无声胜有声"的拉扯感。请分析现有片段（如教室独白、阳台看星）中，哪些细节已经具备了这种美感，哪些地方过于直白或破碎。

### 实质性建议
1. 关于"缺口"：不要告诉我缺了什么情节，要告诉我缺了什么情绪。例如：男女主现在是否在"假装正常"？这种伪装在哪里会出现裂痕？

2. 关于"场景"：不要建议生硬的"老年大学"或"修图软件界面"。请结合他们创业者和职场人的身份，在"深夜加班"、"通勤路上"、"应酬后的独处"等现实场景中，设计符合"反套路霸总"和"悲悯自省者"人设的互动细节。

3. 关于"修改方向"：针对缺口分析中的"深夜陪伴"和"确定关系"，请给出具体的动作描写建议（如：一个眼神，一个递东西的动作、一句没说完的话），而不是概念性的建议。

请按以下格式输出：
## 写作灵感建议

### 1. 情感氛围分析
[用文学语言描述当前情感状态，关注眼神、动作、潜台词等细节]

### 2. 情感断裂带
[分析人物内心未能触达的深层恐惧或渴望，哪里卡住了？]

### 3. 场景建议
[基于现有场景（教室、阳台、酒吧、公司等）的逻辑延伸，设计具体互动细节]

### 4. 具体动作建议
[给出可操作的写作建议：一个眼神、一个递东西的动作、一句没说完的话]
"""

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": "你是一位资深文学编辑或小说家，擅长用文学语言提供写作指导，拒绝学术黑话，注重画面感和情绪流动。",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content


def save_brainstorming(
    analysis_results: list[dict],
    hints: list[dict],
    llm_suggestions: str,
    gaps: list[dict],
):
    """保存头脑风暴结果"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 保存详细分析结果
    analysis_path = OUTPUT_DIR / "analysis_detail.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "fragments_analysis": analysis_results,
                "hints": hints,
                "uncovered_outlines": gaps,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    # 保存 Markdown 报告
    report_path = OUTPUT_DIR / "brainstorming_report.md"

    lines = ["# 写作灵感头脑风暴报告\n"]

    # 1. 片段分析摘要 - 表格格式
    lines.append("## 1. 片段分析摘要\n")
    lines.append("| 片段 | 关键词 | 场景 | 相关提纲 | 相关初稿 |\n")
    lines.append("|------|--------|------|----------|----------|\n")
    for result in analysis_results:
        keywords = ", ".join(result["keywords"][:3])
        locations = ", ".join(result["locations"]) if result["locations"] else "-"
        outlines = ", ".join([t[2] for t in result["outline_related"][:2]])
        drafts = ", ".join([t[2] for t in result["draft_related"][:2]])
        lines.append(
            f"| {result['title']} | {keywords} | {locations} | {outlines} | {drafts} |\n"
        )

    lines.append("\n---\n")

    # 2. 缺口分析 - 简化格式
    lines.append("## 2. 缺口分析\n")
    lines.append("以下提纲设定尚未在当前小说中实现：\n")
    for i, gap in enumerate(gaps, 1):
        lines.append(f"**{i}. {gap['title']}**\n")
        content_preview = gap["content"][:150].replace("\n", " ")
        lines.append(f"_{content_preview}..._\n\n")

    lines.append("\n---\n")

    # 3. 写作备选清单 - 新增
    lines.append("## 3. 写作备选清单\n")

    # 基于缺口
    lines.append("### 基于缺口的写作候选\n")
    for i, gap in enumerate(gaps[:5], 1):
        lines.append(f"{i}. **{gap['title']}**\n")

    # 基于场景建议
    lines.append("\n### 场景候选\n")
    scenes = [
        "校史馆修复室 - 承接教室场景，修复老照片发现偷拍侧影",
        "凌晨孵化器监控屏前 - 早起独坐的职场镜像，算法伦理争议",
        "台风天社区图书馆 - 公共空间临时结盟，共守《小王子》",
    ]
    for i, scene in enumerate(scenes, 1):
        lines.append(f"{i}. {scene}\n")

    # 情感阶段
    lines.append("\n### 情感阶段建议\n")
    lines.append("- 当前阶段: 教室独白 → 阳台/酒吧 → 日常共生\n")
    lines.append("- 下一步: 触发「低熵启动事件」- 日常主权让渡\n")

    lines.append("\n---\n")

    # 4. LLM 写作建议
    lines.append("## 4. LLM 写作建议\n")
    lines.append(llm_suggestions)

    report_path.write_text("".join(lines), encoding="utf-8")
    print(f"\n报告已保存至: {report_path}")

    return report_path


def main():
    print("=" * 50)
    print("头脑风暴器启动")
    print("=" * 50)

    # 1. 加载数据
    knowl_data = load_knowledge_base()
    novel_data = load_novel_summary()

    # 2. 分析每个写作片段
    print("\n分析写作片段...")
    analysis_results = []
    for fragment in novel_data["fragments"]:
        result = analyze_fragment(fragment, knowl_data)
        analysis_results.append(result)
        print(
            f"  - {result['title']}: {len(result['outline_related'])} 个相关提纲, {len(result['draft_related'])} 个相关初稿"
        )

    # 3. 缺口分析
    print("\n进行缺口分析...")
    gaps = find_gaps(analysis_results, knowl_data)
    print(f"  - 发现 {len(gaps)} 个未覆盖的提纲设定")

    # 4. 生成基础建议
    print("\n生成灵感建议...")
    hints = generate_hints(analysis_results, knowl_data)

    # 5. LLM 深度建议
    print("调用 LLM 生成深度建议...")
    llm_suggestions = suggest_with_llm(analysis_results, knowl_data, novel_data)

    # 6. 保存结果
    print("\n保存结果...")
    save_brainstorming(analysis_results, hints, llm_suggestions, gaps)

    print("\n完成！")


if __name__ == "__main__":
    main()

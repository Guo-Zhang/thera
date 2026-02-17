"""
审计脚本 - 元认知浓度分析

输入：项目根目录 AGENTS.md
算法：LLM 检查 AGENTS.md 的元认知浓度
输出：scripts/reports 文件夹
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json
from datetime import datetime
from typing import Any

from openai import OpenAI

from thera.config import settings


def create_llm_client() -> OpenAI:
    return OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)


META_COGNITION_PROMPT = """请分析以下文档的元认知浓度。元认知是指"对思考的思考"，包括：

1. 自我意识：是否包含对自身行为的反思和描述
2. 策略意识：是否包含对方法、策略的明确说明
3. 监控意识：是否包含对进度、状态的监控描述
4. 评估意识：是否包含对效果、质量的评估标准
5. 调整意识：是否包含对计划的调整和优化

请对以下文档进行评分（1-10分），并给出详细的分析报告：

---

{content}

---

请以 JSON 格式返回分析结果：
{{
    "meta_cognition_score": <1-10的分数>,
    "self_awareness": <1-10分数>,
    "strategy_awareness": <1-10分数>,
    "monitoring_awareness": <1-10分数>,
    "evaluation_awareness": <1-10分数>,
    "adjustment_awareness": <1-10分数>,
    "strengths": ["优势1", "优势2"],
    "weaknesses": ["劣势1", "劣势2"],
    "recommendations": ["建议1", "建议2"]
}}
"""


def analyze_meta_cognition(content: str, client: OpenAI) -> dict[str, Any]:
    """使用 LLM 分析元认知浓度"""
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": "你是一个专业的元认知分析师，擅长评估文档中的元认知浓度。",
            },
            {
                "role": "user",
                "content": META_COGNITION_PROMPT.format(content=content[:8000]),
            },
        ],
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    return result


def run_thera_activity(
    agents_file: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """运行 AI 外脑活动

    Args:
        agents_file: AGENTS.md 文件路径
        output_dir: 输出目录
    """
    root_dir = Path(__file__).parent.parent

    if agents_file is None:
        agents_file = root_dir / "AGENTS.md"

    if output_dir is None:
        output_dir = root_dir / "docs" / "ops" / "reports"

    output_dir.mkdir(parents=True, exist_ok=True)

    if not agents_file.exists():
        raise FileNotFoundError(f"AGENTS.md not found: {agents_file}")

    content = agents_file.read_text(encoding="utf-8")
    print(f"加载了 AGENTS.md ({len(content)} 字符)")

    client = create_llm_client()

    print("分析元认知浓度...")
    analysis = analyze_meta_cognition(content, client)

    result = {
        "timestamp": datetime.now().isoformat(),
        "agents_file": str(agents_file),
        "analysis": analysis,
    }

    report_file = output_dir / "report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"元认知浓度得分: {analysis.get('meta_cognition_score', 'N/A')}/10")
    print(f"分析报告已保存到: {report_file}")

    return result


if __name__ == "__main__":
    run_thera_activity()

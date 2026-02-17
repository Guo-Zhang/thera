"""
审计脚本 - Thera 系统自画像

基于 Vibe Coding 范式，用观测工具分析 Thera 自身：
1. radon - 圈复杂度分析
2. vulture - 僵尸代码检测
3. pyan3 - 依赖图分析
4. LLM - 元认知浓度分析

输入：项目 src/ 目录
输出：docs/ops/reports/
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openai import OpenAI
from thera.config import settings


def create_llm_client() -> OpenAI:
    return OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)


def run_command(cmd: list[str], cwd: Path | None = None) -> str:
    """运行命令并返回输出"""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=60
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"


def analyze_complexity(root_dir: Path) -> dict[str, Any]:
    """用 radon 分析圈复杂度"""
    print("  [1/4] 分析圈复杂度...")
    try:
        result = run_command(["radon", "cc", "-s", "src/thera"], cwd=root_dir)
        lines = result.strip().split("\n")
        functions = []
        for line in lines:
            if "F " in line or "M " in line:
                parts = line.strip().split()
                if len(parts) >= 3:
                    func_name = parts[2] if ":" not in parts[2] else parts[1]
                    try:
                        complexity = int(parts[1].split(":")[-1])
                        functions.append(
                            {"function": func_name, "complexity": complexity}
                        )
                    except:
                        pass
        functions.sort(key=lambda x: x["complexity"], reverse=True)
        return {"hotspots": functions[:10], "raw": result[:2000]}
    except FileNotFoundError:
        return {"error": "radon not installed", "hotspots": []}


def analyze_dead_code(root_dir: Path) -> dict[str, Any]:
    """用 vulture 检测僵尸代码"""
    print("  [2/4] 检测僵尸代码...")
    try:
        result = run_command(
            ["vulture", "src/thera", "--min-confidence=80"], cwd=root_dir
        )
        lines = [l for l in result.strip().split("\n") if l and not l.startswith("===")]
        unused = []
        for line in lines[:20]:
            if "unused" in line.lower():
                unused.append(line.strip())
        return {"unused_code": unused, "raw": result[:2000]}
    except FileNotFoundError:
        return {"error": "vulture not installed", "unused_code": []}


def analyze_dependencies(root_dir: Path) -> dict[str, Any]:
    """用 pyan3 分析依赖图"""
    print("  [3/4] 分析依赖关系...")
    try:
        src_files = list(root_dir.glob("src/thera/**/*.py"))
        src_files = [f for f in src_files if f.name != "__init__.py"]
        if not src_files:
            return {"error": "No source files found"}

        cmd = [
            "pyan3",
            *[str(f.relative_to(root_dir)) for f in src_files[:10]],
            "--uses",
            "--no-defines",
            "--colored",
        ]
        result = run_command(cmd, cwd=root_dir)

        lines = result.strip().split("\n")
        deps = []
        for line in lines[:30]:
            if " uses " in line or " provides " in line:
                deps.append(line.strip())

        return {"dependencies": deps, "raw": result[:3000]}
    except FileNotFoundError:
        return {"error": "pyan3 not installed", "dependencies": []}


def analyze_meta_cognition(root_dir: Path, client: OpenAI) -> dict[str, Any]:
    """用 LLM 分析元认知浓度"""
    print("  [4/4] 分析元认知浓度...")

    agents_file = root_dir / "AGENTS.md"
    if not agents_file.exists():
        return {"error": "AGENTS.md not found"}

    content = agents_file.read_text(encoding="utf-8")

    prompt = f"""请分析以下 AGENTS.md 文档的元认知浓度。

元认知是指"对思考的思考"，包括：
1. 自我意识：是否包含对自身行为的反思和描述
2. 策略意识：是否包含对方法、策略的明确说明
3. 监控意识：是否包含对进度、状态的监控描述
4. 评估意识：是否包含对效果、质量的评估标准
5. 调整意识：是否包含对计划的调整和优化

文档内容：
---
{content[:6000]}
---

请以 JSON 格式返回分析结果：
{{
    "meta_cognition_score": <1-10分数>,
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

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "你是一个专业的元认知分析师。"},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}


def generate_report(
    complexity: dict,
    dead_code: dict,
    dependencies: dict,
    meta_cognition: dict,
    output_dir: Path,
) -> str:
    """生成审计报告"""
    from datetime import datetime

    md = [
        "# Thera 系统自画像",
        "",
        f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 1. 复杂度热点 (Radon)",
        "",
    ]

    if complexity.get("hotspots"):
        md.append("| 函数 | 复杂度 |")
        md.append("| --- | --- |")
        for f in complexity["hotspots"][:8]:
            md.append(f"| {f['function']} | {f['complexity']} |")
    else:
        md.append(f"_{complexity.get('error', '无数据')}_")

    md.extend(["", "## 2. 僵尸代码 (Vulture)", ""])
    if dead_code.get("unused_code"):
        for item in dead_code["unused_code"][:10]:
            md.append(f"- {item}")
    else:
        md.append(f"_{dead_code.get('error', '无僵尸代码')}_")

    md.extend(["", "## 3. 依赖关系 (Pyan3)", ""])
    if dependencies.get("dependencies"):
        for dep in dependencies["dependencies"][:10]:
            md.append(f"- {dep}")
    else:
        md.append(f"_{dependencies.get('error', '无依赖数据')}_")

    md.extend(["", "## 4. 元认知浓度 (LLM)", ""])
    if meta_cognition and not meta_cognition.get("error"):
        md.append(f"**总分: {meta_cognition.get('meta_cognition_score', 'N/A')}/10**")
        md.append("")
        md.append(f"- 自我意识: {meta_cognition.get('self_awareness', '-')}/10")
        md.append(f"- 策略意识: {meta_cognition.get('strategy_awareness', '-')}/10")
        md.append(f"- 监控意识: {meta_cognition.get('monitoring_awareness', '-')}/10")
        md.append(f"- 评估意识: {meta_cognition.get('evaluation_awareness', '-')}/10")
        md.append(f"- 调整意识: {meta_cognition.get('adjustment_awareness', '-')}/10")
        md.append("")
        md.append("**优势:**")
        for s in meta_cognition.get("strengths", []):
            md.append(f"- {s}")
        md.append("")
        md.append("**建议:**")
        for r in meta_cognition.get("recommendations", []):
            md.append(f"- {r}")
    else:
        md.append(f"_{meta_cognition.get('error', '分析失败')}_")

    report_path = output_dir / "system_audit.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    return str(report_path)


def run_audit(
    src_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """运行审计"""
    root_dir = Path(__file__).parent.parent

    if src_dir is None:
        src_dir = root_dir / "src"

    if output_dir is None:
        output_dir = root_dir / "docs" / "ops" / "reports"

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Thera 系统自画像 ===")
    print(f"源码目录: {src_dir}")

    complexity = analyze_complexity(root_dir)
    dead_code = analyze_dead_code(root_dir)
    dependencies = analyze_dependencies(root_dir)

    client = create_llm_client()
    meta_cognition = analyze_meta_cognition(root_dir, client)

    report_path = generate_report(
        complexity, dead_code, dependencies, meta_cognition, output_dir
    )

    result = {
        "timestamp": datetime.now().isoformat(),
        "complexity": complexity,
        "dead_code": dead_code,
        "dependencies": dependencies,
        "meta_cognition": meta_cognition,
    }

    json_path = output_dir / "audit_result.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n报告已保存: {report_path}")
    print(f"JSON数据: {json_path}")

    return result


if __name__ == "__main__":
    run_audit()

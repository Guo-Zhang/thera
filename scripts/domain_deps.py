"""
Domain 依赖分析器 - 基于 AST

分析 Domain 模块间的依赖关系：
1. 导入依赖 - 每个 Domain 导入哪些模块
2. 调用依赖 - Domain 间的方法调用关系
3. 继承关系 - Domain 与基类的关系
4. 循环依赖检测

输出：docs/ops/reports/domain_dependency_analysis.md
"""

import ast
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_file(file_path: Path) -> ast.AST | None:
    """解析 Python 文件为 AST"""
    try:
        return ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  解析错误 {file_path}: {e}")
        return None


def extract_imports(tree: ast.AST, file_path: str) -> dict[str, list[str]]:
    """提取导入语句"""
    imports = {"from_import": [], "import": []}

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                name = alias.asname or alias.name
                imports["from_import"].append(
                    {
                        "module": module,
                        "name": name,
                        "full": f"{module}.{name}" if module else name,
                    }
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name
                imports["import"].append({"module": name, "full": name})

    return imports


def extract_class_inheritance(tree: ast.AST) -> list[dict[str, str]]:
    """提取类继承关系"""
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(base.attr)
                else:
                    bases.append("Unknown")
            classes.append({"name": node.name, "bases": bases})
    return classes


def extract_method_calls(tree: ast.AST) -> list[dict[str, Any]]:
    """提取方法调用"""
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                caller = node.func.value
                if isinstance(caller, ast.Name):
                    calls.append(
                        {
                            "caller": caller.id,
                            "method": node.func.attr,
                            "type": "attribute",
                        }
                    )
            elif isinstance(node.func, ast.Name):
                calls.append(
                    {"caller": None, "method": node.func.id, "type": "function"}
                )
    return calls


def extract_function_defs(tree: ast.AST) -> list[dict[str, Any]]:
    """提取函数定义"""
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [arg.arg for arg in node.args.args]
            functions.append(
                {
                    "name": node.name,
                    "args": args,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "line": node.lineno,
                }
            )
    return functions


def analyze_domain(file_path: Path) -> dict[str, Any]:
    """分析单个 Domain 文件"""
    tree = parse_file(file_path)
    if not tree:
        return {}

    return {
        "file": str(file_path),
        "imports": extract_imports(tree, str(file_path)),
        "classes": extract_class_inheritance(tree),
        "functions": extract_function_defs(tree),
        "method_calls": extract_method_calls(tree),
    }


def build_dependency_graph(domain_analysis: dict[str, dict]) -> dict[str, Any]:
    """构建依赖图"""
    domain_names = list(domain_analysis.keys())
    edges = []

    for domain, data in domain_analysis.items():
        imports = data.get("imports", {}).get("from_import", []) + data.get(
            "imports", {}
        ).get("import", [])

        for imp in imports:
            imp_name = imp.get("name", "")
            imp_module = imp.get("module", "")

            for other_domain in domain_names:
                if other_domain == domain:
                    continue
                if (
                    other_domain in imp_name.lower()
                    or other_domain in imp_module.lower()
                ):
                    edges.append(
                        {
                            "from": domain,
                            "to": other_domain,
                            "type": "import",
                            "detail": f"{imp_module}.{imp_name}"
                            if imp_module
                            else imp_name,
                        }
                    )

    return {"nodes": domain_names, "edges": edges}


def detect_circular_dependencies(edges: list[dict]) -> list[list[str]]:
    """检测循环依赖"""
    graph = defaultdict(list)
    for edge in edges:
        graph[edge["from"]].append(edge["to"])

    def has_cycle(node, visited, rec_stack, path):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph[node]:
            if neighbor not in visited:
                if has_cycle(neighbor, visited, rec_stack, path):
                    return True
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                return path[cycle_start:]

        path.pop()
        rec_stack.remove(node)
        return False

    cycles = []
    visited = set()
    for node in graph:
        if node not in visited:
            path = []
            cycle = has_cycle(node, visited, set(), path)
            if cycle:
                cycles.append(cycle)

    return cycles


def analyze_cross_domain_calls(
    domain_analysis: dict[str, dict],
) -> list[dict[str, Any]]:
    """分析跨 Domain 调用"""
    calls = []
    domain_names = {d.lower() for d in domain_analysis.keys()}

    for domain, data in domain_analysis.items():
        for call in data.get("method_calls", []):
            method = call.get("method", "")
            if any(name in method.lower() for name in domain_names):
                calls.append({"from": domain, "to": method, "type": call.get("type")})

    return calls


def generate_report(
    analysis: dict[str, dict],
    graph: dict,
    cycles: list[list[str]],
    cross_calls: list[dict],
    output_dir: Path,
) -> str:
    """生成分析报告"""
    md = [
        "# Domain 依赖分析报告",
        "",
        f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 1. Domain 概览",
        "",
        "| Domain | 类 | 函数数 | 导入数 |",
        "| --- | --- | --- | --- |",
    ]

    for domain, data in analysis.items():
        classes = [c["name"] for c in data.get("classes", [])]
        funcs = len(data.get("functions", []))
        imports = len(data.get("imports", {}).get("from_import", [])) + len(
            data.get("imports", {}).get("import", [])
        )
        md.append(
            f"| {domain} | {', '.join(classes) if classes else '-'} | {funcs} | {imports} |"
        )

    md.extend(["", "## 2. 导入依赖详情", ""])

    for domain, data in analysis.items():
        imports = data.get("imports", {})
        from_imports = imports.get("from_import", [])
        stdlib_imports = [
            i for i in from_imports if not i["module"].startswith("thera")
        ]
        thera_imports = [i for i in from_imports if i["module"].startswith("thera")]

        md.append(f"### {domain}")
        md.append("")

        if thera_imports:
            md.append("**Thera 内部导入:**")
            for imp in thera_imports:
                md.append(f"- `{imp['module']}.{imp['name']}`")
            md.append("")

        if stdlib_imports:
            md.append(f"**标准库/第三方导入:** {len(stdlib_imports)} 个")
            md.append("")

    md.extend(["", "## 3. 依赖图", ""])

    if graph.get("edges"):
        md.append("```mermaid")
        md.append("graph LR")
        for edge in graph["edges"]:
            md.append(f"    {edge['from']} --> {edge['to']}")
        md.append("```")
    else:
        md.append("_无显式 Domain 间导入依赖_")

    md.extend(["", "## 4. 循环依赖检测", ""])

    if cycles:
        md.append("⚠️ **发现循环依赖:**")
        for cycle in cycles:
            md.append(f"- {' -> '.join(cycle)}")
    else:
        md.append("✅ **无循环依赖**")

    md.extend(["", "## 5. 跨 Domain 调用", ""])

    if cross_calls:
        for call in cross_calls:
            md.append(f"- {call['from']} -> {call['to']}")
    else:
        md.append("_无跨 Domain 方法调用_")

    md.extend(["", "## 6. 分析洞察", ""])

    domain_imports = {
        d: len(a.get("imports", {}).get("from_import", [])) for d, a in analysis.items()
    }
    most_dependent = (
        max(domain_imports, key=domain_imports.get) if domain_imports else None
    )

    md.append(
        f"- **依赖最多**: {most_dependent} ({domain_imports.get(most_dependent, 0)} 个导入)"
    )

    external_deps = {}
    for domain, data in analysis.items():
        imports = data.get("imports", {}).get("from_import", [])
        external = [
            i["module"].split(".")[0]
            for i in imports
            if not i["module"].startswith("thera")
        ]
        external_deps[domain] = set(external)

    md.append("")
    md.append("**外部依赖:**")
    for domain, deps in external_deps.items():
        if deps:
            md.append(f"- {domain}: {', '.join(sorted(deps))}")

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "domain_dependency_analysis.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    return str(report_path)


def run_domain_analysis(output_dir: Path | None = None) -> dict[str, Any]:
    """运行 Domain 依赖分析"""
    root_dir = Path(__file__).parent.parent
    domain_dir = root_dir / "src" / "thera" / "domain"

    if output_dir is None:
        output_dir = root_dir / "docs" / "ops" / "reports"

    print("=== Domain 依赖分析 ===")
    print(f"Domain 目录: {domain_dir}")

    domain_files = list(domain_dir.glob("*.py"))
    domain_files = [f for f in domain_files if f.name != "__init__.py"]

    analysis = {}
    for f in domain_files:
        domain_name = f.stem.replace("Domain", "")
        print(f"  分析: {domain_name}")
        analysis[domain_name] = analyze_domain(f)

    graph = build_dependency_graph(analysis)
    cycles = detect_circular_dependencies(graph.get("edges", []))
    cross_calls = analyze_cross_domain_calls(analysis)

    report_path = generate_report(analysis, graph, cycles, cross_calls, output_dir)

    result = {
        "timestamp": datetime.now().isoformat(),
        "domains": list(analysis.keys()),
        "graph": graph,
        "circular_dependencies": cycles,
        "cross_domain_calls": cross_calls,
    }

    json_path = output_dir / "domain_dependency.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n报告: {report_path}")
    print(f"JSON: {json_path}")

    return result


if __name__ == "__main__":
    run_domain_analysis()

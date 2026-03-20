"""vital 数据读取模块"""

import yaml
from pathlib import Path

# 默认数据路径（主仓库 meta/ 目录）
DEFAULT_DATA_PATH = Path(__file__).parent.parent.parent.parent.parent / "meta"


def load_submodules(data_path: Path = None) -> list[dict]:
    """读取 submodules.yaml

    Args:
        data_path: meta/ 目录路径，默认为 ../../../../meta

    Returns:
        子模块列表，每个元素包含 name, path, category, description 等字段
    """
    if data_path is None:
        data_path = DEFAULT_DATA_PATH

    yaml_path = data_path / "profile" / "submodules.yaml"
    if not yaml_path.exists():
        return []

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    return data.get("submodules", [])


def get_submodules_by_category(
    submodules: list[dict], category: str = None
) -> list[dict]:
    """按分类过滤子模块

    Args:
        submodules: 子模块列表
        category: 分类过滤（procedural/declarative），None 表示不过滤

    Returns:
        过滤后的子模块列表
    """
    if category is None:
        return submodules
    return [s for s in submodules if s.get("category") == category]


def get_category_label(category: str) -> str:
    """获取分类的中文标签"""
    labels = {
        "procedural": "程序型",
        "declarative": "陈述型",
    }
    return labels.get(category, category)


def get_grid_label(grid: str) -> str:
    """获取九宫格位置的中文标签"""
    labels = {
        "past-event": "过去-事件",
        "past-semantic": "过去-语义",
        "past-self": "过去-自我",
        "present-event": "现在-事件",
        "present-semantic": "现在-语义",
        "present-self": "现在-自我",
        "future-event": "未来-事件",
        "future-semantic": "未来-语义",
        "future-self": "未来-自我",
    }
    return labels.get(grid, grid)


def get_type_label(type_: str) -> str:
    """获取程序型类型的中文标签"""
    labels = {
        "platform": "平台",
        "customary-law": "习惯法",
        "authoritative-law": "权威法理",
        "statute-law": "成文法",
        "case-law": "判例法",
    }
    return labels.get(type_, type_)

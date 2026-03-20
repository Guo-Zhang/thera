"""vital 数据读取模块"""

import json
import yaml
from pathlib import Path

# 默认数据路径
VITAL_DATA_PATH = Path(__file__).parent / "data"
META_DATA_PATH = Path(__file__).parent.parent.parent.parent.parent / "meta"


def load_submodules(data_path: Path = None) -> list[dict]:
    """读取 submodules.yaml

    Args:
        data_path: meta/ 目录路径，默认为 ../../../../meta

    Returns:
        子模块列表，每个元素包含 name, path, category, description 等字段
    """
    if data_path is None:
        data_path = META_DATA_PATH

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


# ==================== 转换过程数据 ====================


def load_raw_journal(date: str, data_path: Path = None) -> str:
    """加载原始日志

    Args:
        date: 日期字符串，格式 YYYY-MM-DD
        data_path: 数据目录路径

    Returns:
        原始日志内容
    """
    if data_path is None:
        data_path = VITAL_DATA_PATH / "sample"

    raw_path = data_path / "raw" / f"{date}.md"
    if not raw_path.exists():
        return ""

    return raw_path.read_text()


def load_episode(date: str, data_path: Path = None) -> list[dict]:
    """加载提炼后事件记忆

    Args:
        date: 日期字符串，格式 YYYY-MM-DD
        data_path: 数据目录路径

    Returns:
        事件记忆列表，每个元素包含 id, title, description, tense, type
    """
    if data_path is None:
        data_path = VITAL_DATA_PATH / "sample"

    episode_path = data_path / "episode" / f"{date}.jsonl"
    if not episode_path.exists():
        return []

    episodes = []
    with open(episode_path) as f:
        for line in f:
            line = line.strip()
            if line:
                episodes.append(json.loads(line))

    return episodes


def get_tense_label(tense: str) -> str:
    """获取时态的中文标签"""
    labels = {
        "past": "过去",
        "present": "现在",
        "future": "未来",
    }
    return labels.get(tense, tense)


def get_event_type_label(event_type: str) -> str:
    """获取事件类型的中文标签"""
    labels = {
        "decision": "决策",
        "plan": "计划",
        "report": "报告",
        "evaluation": "评估",
        "retrospective": "复盘",
    }
    return labels.get(event_type, event_type)


def get_available_dates(data_path: Path = None) -> list[str]:
    """获取可用的日期列表

    Returns:
        日期字符串列表，按日期倒序排列
    """
    if data_path is None:
        data_path = VITAL_DATA_PATH / "sample"

    raw_dir = data_path / "raw"
    if not raw_dir.exists():
        return []

    dates = []
    for f in raw_dir.glob("*.md"):
        date = f.stem
        if date.count("-") == 2:  # YYYY-MM-DD 格式
            dates.append(date)

    return sorted(dates, reverse=True)

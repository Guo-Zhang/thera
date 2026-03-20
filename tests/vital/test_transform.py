"""转换过程数据读取测试"""

from vital.data import (
    load_raw_journal,
    load_episode,
    get_available_dates,
    get_tense_label,
    get_event_type_label,
)


def test_load_raw_journal():
    """测试加载原始日志"""
    raw = load_raw_journal("2026-03-20")
    assert "九宫格" in raw
    assert "Kivy" in raw


def test_load_episode():
    """测试加载提炼后事件记忆"""
    episodes = load_episode("2026-03-20")
    assert len(episodes) == 5

    # 检查第一个事件
    first = episodes[0]
    assert first["title"] == "九宫格模型确认"
    assert first["tense"] == "present"
    assert first["type"] == "evaluation"


def test_get_available_dates():
    """测试获取可用日期"""
    dates = get_available_dates()
    assert "2026-03-20" in dates
    assert dates == sorted(dates, reverse=True)  # 倒序排列


def test_get_tense_label():
    """测试时态标签"""
    assert get_tense_label("past") == "过去"
    assert get_tense_label("present") == "现在"
    assert get_tense_label("future") == "未来"
    assert get_tense_label("unknown") == "unknown"


def test_get_event_type_label():
    """测试事件类型标签"""
    assert get_event_type_label("decision") == "决策"
    assert get_event_type_label("plan") == "计划"
    assert get_event_type_label("report") == "报告"
    assert get_event_type_label("evaluation") == "评估"
    assert get_event_type_label("retrospective") == "复盘"
    assert get_event_type_label("unknown") == "unknown"


def test_load_nonexistent_date():
    """测试加载不存在的日期"""
    raw = load_raw_journal("2000-01-01")
    assert raw == ""

    episodes = load_episode("2000-01-01")
    assert episodes == []

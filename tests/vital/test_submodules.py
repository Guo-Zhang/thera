"""子模块数据读取测试"""

from pathlib import Path

from vital.data import (
    load_submodules,
    get_submodules_by_category,
    get_category_label,
    get_grid_label,
    get_type_label,
)


# 测试数据路径
DATA_PATH = Path(__file__).parent.parent.parent.parent.parent / "meta"


def test_load_submodules():
    """测试加载子模块"""
    subs = load_submodules(DATA_PATH)
    assert len(subs) == 12
    assert subs[0]["name"] == "thera"
    assert subs[0]["category"] == "procedural"


def test_load_submodules_default_path():
    """测试默认路径加载"""
    subs = load_submodules()
    assert len(subs) == 12


def test_get_submodules_by_category():
    """测试按分类过滤"""
    subs = load_submodules(DATA_PATH)

    procedural = get_submodules_by_category(subs, "procedural")
    assert all(s["category"] == "procedural" for s in procedural)

    declarative = get_submodules_by_category(subs, "declarative")
    assert all(s["category"] == "declarative" for s in declarative)

    all_subs = get_submodules_by_category(subs, None)
    assert len(all_subs) == len(subs)


def test_get_category_label():
    """测试分类标签"""
    assert get_category_label("procedural") == "程序型"
    assert get_category_label("declarative") == "陈述型"
    assert get_category_label("unknown") == "unknown"


def test_get_grid_label():
    """测试九宫格标签"""
    assert get_grid_label("past-event") == "过去-事件"
    assert get_grid_label("present-semantic") == "现在-语义"
    assert get_grid_label("unknown") == "unknown"


def test_get_type_label():
    """测试程序型类型标签"""
    assert get_type_label("platform") == "平台"
    assert get_type_label("customary-law") == "习惯法"
    assert get_type_label("unknown") == "unknown"

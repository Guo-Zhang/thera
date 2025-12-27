"""
Test cases for the reasoner module.
"""

import json
from pathlib import Path
from unittest.mock import patch
import pytest

from src.thera.models import Method, Memory
from src.thera.reasoner import Reasoner
from utils.myst_parser import parse_myst_use_case

# --- Fixture 路径 ---
USE_CASE_MD = Path(__file__).parent.parent / "docs/use_cases/uc_01_extract_location_mapping.md"
FIXTURES_DIR = Path(__file__).parent.parent / "docs/fixtures"

@pytest.fixture
def uc01_metadata():
    return parse_myst_use_case(USE_CASE_MD)

@pytest.fixture
def uc01_method():
    template = (FIXTURES_DIR / "uc01_prompt_template.txt").read_text()
    return Method(name="extract_location_mapping", prompt_template=template)

@pytest.fixture
def uc01_input_memory():
    raw = (FIXTURES_DIR / "uc01_user_input.txt").read_text()
    return Memory(id="test-input", content={"raw": raw})

@pytest.fixture
def uc01_expected_output():
    return json.loads((FIXTURES_DIR / "uc01_expected_memory.json").read_text())

def test_uc01_extract_location_mapping_success(
    uc01_method,
    uc01_input_memory,
    uc01_expected_output
):
    # 模拟 LLM 返回期望的 JSON 字符串
    expected_json_str = json.dumps(uc01_expected_output, ensure_ascii=False)

    with patch.object(Reasoner, '_call_llm', return_value=expected_json_str):
        result = Reasoner.reason(uc01_method, uc01_input_memory)

    # 断言结构完全匹配
    assert result == uc01_expected_output
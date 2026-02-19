"""
quanttide-apple pytest 配置

环境变量:
    APPLE_USE_MOCK: 设置为 "true" 使用 mock，默认使用真实 API
"""

import os
import pytest

APPLE_USE_MOCK = os.getenv("APPLE_USE_MOCK", "false").lower() == "true"


@pytest.fixture
def is_mock():
    """是否使用 mock（默认使用真实 API）"""
    return APPLE_USE_MOCK

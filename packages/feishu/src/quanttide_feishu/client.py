"""
飞书客户端
"""

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def create_lark_client() -> Any:
    """创建飞书 API 客户端"""
    from lark_oapi import Client

    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")

    if not app_id or not app_secret:
        raise ValueError("FEISHU_APP_ID and FEISHU_APP_SECRET must be set")

    return (
        Client.builder()
        .app_id(app_id)
        .app_secret(app_secret)
        .log_level(1)  # INFO
        .build()
    )

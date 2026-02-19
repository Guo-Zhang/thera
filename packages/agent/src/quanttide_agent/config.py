"""
配置模块
"""

from typing import Optional


class Settings:
    """AIGC 配置"""

    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4"
    llm_embedding_model: str = "text-embedding-3-small"

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
        _load_from_env(_settings)
    return _settings


def _load_from_env(settings: Settings):
    """从环境变量加载配置"""
    import os

    settings.llm_api_key = os.getenv("LLM_API_KEY", "")
    settings.llm_base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    settings.llm_model = os.getenv("LLM_MODEL", "gpt-4")
    settings.llm_embedding_model = os.getenv(
        "LLM_EMBEDDING_MODEL", "text-embedding-3-small"
    )

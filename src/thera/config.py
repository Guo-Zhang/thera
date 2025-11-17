"""
配置管理模块

封装项目的配置管理，集成环境变量和默认设置。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """项目配置设置"""
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # 数据库配置
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str = 'neo4j'

    # LLM 配置
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    llm_embedding_model: str
    llm_reranker_model: str


# 全局配置实例
settings = Settings()
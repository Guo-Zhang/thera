from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 环境变量
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str = "neo4j"
    neo4j_index_name: str = "thera"

    llm_api_key: str
    llm_base_url: str
    llm_model: str
    llm_embedding_model: str
    llm_reranker_model: str


settings = Settings()


if __name__ == "__main__":
    # 验证环境变量已被正确导入
    print(settings.model_dump())

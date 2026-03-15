from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def get_platform_root() -> Path:
    return Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(get_platform_root() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    opencode_path: str


settings = Settings()


if __name__ == "__main__":
    # 验证环境变量已被正确导入
    print(settings.model_dump())

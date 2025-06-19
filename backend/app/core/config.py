# アプリケーションの設定を管理するファイル
# Pydanticを使用して、環境変数から設定を読み込む
import enum
from typing import Any, Optional
from pydantic import PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(str, enum.Enum):
    DEVELOP = "development"
    PRODUCTION = "production"


class Settings(BaseSettings):
    # 明示的に環境変数を読み込む（Pydanticv2以降）
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    
    ENVIRONMENT: AppEnvironment

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "app"

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # OpenAI API設定
    API_KEY: str

    SECRET_KEY: str
    ALGORITHM: str

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="after")
    def assemble_db_connection(cls, v: Optional[str], values: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        
        return str(
            PostgresDsn.build(
                scheme="postgresql",
                username=values.data.get("POSTGRES_USER"),
                password=values.data.get("POSTGRES_PASSWORD"),
                host=values.data.get("POSTGRES_SERVER"),
                port=int(values.data.get("POSTGRES_PORT")),
                path=f"{values.data.get('POSTGRES_DB') or ''}",
            )
        )


settings = Settings()
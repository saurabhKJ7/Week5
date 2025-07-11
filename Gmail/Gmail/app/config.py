from functools import lru_cache
import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Base paths
    base_dir: str = Field(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env="BASE_DIR"
    )

    # Gmail OAuth settings
    google_client_id: Optional[str] = Field(None, env="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(None, env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field("http://localhost:8000/oauth2callback", env="GOOGLE_REDIRECT_URI")

    # OpenAI settings
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-3.5-turbo", env="OPENAI_MODEL")

    # Vector DB settings
    vector_db_path: str = Field(
        os.path.join("{base_dir}", "data", "vector_store.index"),
        env="VECTOR_DB_PATH"
    )

    # Redis settings
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    cache_ttl_seconds: int = Field(86400, env="CACHE_TTL_SECONDS")  # 24 hours

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def model_post_init(self, *args, **kwargs):
        # Format paths with base_dir
        self.vector_db_path = self.vector_db_path.format(base_dir=self.base_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings() 
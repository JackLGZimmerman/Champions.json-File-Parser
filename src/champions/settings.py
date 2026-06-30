from functools import lru_cache

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    champions_info_json: HttpUrl


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

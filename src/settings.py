from pydantic_settings import BaseSettings
from pydantic import HttpUrl


class Settings(BaseSettings):
    champion_info_json: HttpUrl

    class Config:
        env_file = ".env"


settings = Settings()

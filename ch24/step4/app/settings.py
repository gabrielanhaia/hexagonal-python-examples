from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ROOMBOOK_")

    database_url: str = "sqlite+aiosqlite:///./roombook.db"
    coinwren_url: str = "https://api.coinwren.example"
    coinwren_api_key: str = ""


settings = Settings()

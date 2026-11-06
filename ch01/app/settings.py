from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ROOMBOOK_")

    database_url: str = "sqlite+aiosqlite:///./roombook.db"
    tillpoint_url: str = "https://api.tillpoint.example"
    tillpoint_api_key: str = ""


settings = Settings()

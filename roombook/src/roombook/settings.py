"""Configuration from ROOMBOOK_* environment variables."""

from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ROOMBOOK_")

    database_url: str = (
        "postgresql+psycopg://roombook:roombook@localhost/roombook"
    )
    kafka_servers: str = "localhost:9092"

    payments: Literal["fake", "tillpoint"] = "fake"
    tillpoint_url: str = "https://api.tillpoint.example"
    tillpoint_api_key: SecretStr = SecretStr("")

    notifier: Literal["console", "smtp"] = "console"
    smtp_host: str = "localhost"
    smtp_port: int = 25
    mail_from: str = "bookings@roombook.example"
    member_address: str = "{member_id}@members.roombook.example"

    log_json: bool = False
    trace_to_console: bool = False

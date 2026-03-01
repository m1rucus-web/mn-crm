from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    avito_internal_key: str = ""
    dadata_api_key: str = ""
    dadata_secret_key: str = ""
    telegram_bot_token: str = ""
    admin_chat_id: str = ""
    crm_db_path: str = "data/crm.db"
    avito_bot_url: str = "http://localhost:8001"
    log_level: str = "INFO"
    app_version: str = "0.1.0"


settings = Settings()

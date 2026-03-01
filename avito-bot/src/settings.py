from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    avito_client_id: str = ""
    avito_client_secret: str = ""
    avito_user_id: str = ""
    openrouter_api_key: str = ""
    whisper_api_key: str = ""
    dadata_api_key: str = ""
    dadata_secret_key: str = ""
    crm_internal_key: str = ""
    crm_url: str = "http://localhost:8003"
    bot_db_path: str = "data/bot.db"
    log_level: str = "INFO"
    app_version: str = "0.1.0"


settings = Settings()

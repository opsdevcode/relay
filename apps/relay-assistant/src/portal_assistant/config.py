from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    database_url: str = "postgresql://portal:portal@localhost:5432/portal"
    redis_url: str = "redis://localhost:6379/0"
    web_origin: str = "http://localhost:3000"
    knowledge_path: str = "/knowledge"
    github_org: str = "opsdevcode"
    github_repo: str = "opsdevcode/relay"


settings = Settings()

from pathlib import Path
from tempfile import gettempdir

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_ingest_checkout_dir() -> str:
    return str(Path(gettempdir()) / "relay-corpus-checkouts")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    # LLM synthesis backend (Phase 1B.4). Empty = auto-detect from credentials below.
    llm_provider: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = ""
    azure_openai_api_version: str = "2024-02-15-preview"
    openai_compatible_base_url: str = ""
    openai_compatible_api_key: str = ""
    openai_compatible_model: str = ""
    database_url: str = "postgresql://portal:portal@localhost:5432/portal"
    redis_url: str = "redis://localhost:6379/0"
    session_ttl_seconds: int = 86_400
    session_max_turns: int = 20
    hybrid_search_enabled: bool = True
    embedding_dimensions: int = 384
    web_origin: str = "http://localhost:3000"
    knowledge_path: str = "/knowledge"
    ingest_checkout_dir: str = Field(default_factory=_default_ingest_checkout_dir)
    ingest_webhook_secret: str = ""
    github_org: str = "opsdevcode"
    github_repo: str = "opsdevcode/relay"
    github_api_token: str = ""
    # When true, trust X-Auth-Request-* from oauth2-proxy behind ingress. Off locally.
    user_context_headers_enabled: bool = False
    # When true, POST /actions/confirm requires entitled IdP groups (see registry tools).
    confirm_action_authorization_enabled: bool = False
    # Fallback allowed groups (comma-separated) when a write tool omits confirm_allowed_groups.
    confirm_allowed_groups: str = ""
    # Sandbox confirm handoff (Phase 2A.2): github_issue | jira | servicenow | url_template
    ticket_intake_provider: str = "github_issue"
    ticket_intake_base_url: str = ""
    ticket_intake_username: str = ""
    ticket_intake_api_token: str = ""
    ticket_intake_project: str = ""
    ticket_intake_issue_type: str = "Task"
    ticket_intake_url_template: str = ""
    observability_provider: str = ""
    grafana_base_url: str = ""
    grafana_dashboard_path_template: str = "/d/{dashboard_uid}?var-service={service}"
    grafana_embed_path_template: str = "/d/{dashboard_uid}?orgId=1&var-service={service}&kiosk"
    grafana_default_dashboard_uid: str = ""
    prometheus_base_url: str = ""
    prometheus_api_token: str = ""
    prometheus_alerts_query_template: str = ""
    prometheus_burn_rate_query_template: str = ""
    audit_log_enabled: bool = True
    audit_query_secret: str = ""


settings = Settings()

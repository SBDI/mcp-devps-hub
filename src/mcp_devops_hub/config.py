from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Loads configuration from environment variables or .env file."""
    model_config = SettingsConfigDict(
        env_prefix="DEVOPS_HUB_", env_file=".env", extra="ignore"
    )

    # Jira
    jira_url: str | None = Field(None, description="URL for Jira instance")
    jira_username: str | None = Field(None, description="Jira username")
    jira_api_token: SecretStr | None = Field(None, description="Jira API token")

    # GitHub
    github_token: SecretStr | None = Field(None, description="GitHub PAT")
    github_base_url: str | None = Field(None, description="GitHub Enterprise URL")

    # CI/CD (Example: Jenkins)
    jenkins_url: str | None = Field(None, description="Jenkins URL")
    jenkins_username: str | None = Field(None, description="Jenkins username")
    jenkins_token: SecretStr | None = Field(None, description="Jenkins API token")
    # Add fields for other CI/CD systems (e.g., GitHub Actions PAT scopes)

    # Notifications
    slack_bot_token: SecretStr | None = Field(None, description="Slack Bot Token")
    teams_default_webhook: str | None = Field(None, description="Default MS Teams Webhook")

    # AI (Optional - if server makes direct LLM calls)
    # llm_api_key: SecretStr | None = Field(None, description="API Key for LLM")
    # llm_model_name: str = "claude-3-5-sonnet-20241022"

    # Groq Configuration
    groq_api_key: SecretStr | None = Field(None, description="Groq API key")
    groq_model_name: str = Field("mixtral-8x7b-32768", description="Groq model name")
    groq_max_tokens: int = Field(32768, description="Maximum tokens for Groq responses")
    groq_temperature: float = Field(0.7, description="Temperature for Groq responses")

# Load settings once
settings = Settings()

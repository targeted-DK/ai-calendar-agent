from pydantic_settings import BaseSettings
from typing import Literal, Optional, List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Provider
    llm_provider: Literal["anthropic", "openai", "gemini", "ollama"] = "anthropic"

    # API Keys (Optional for security validation)
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # Model Selection
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    openai_model: str = "gpt-4-turbo-preview"
    gemini_model: str = "gemini-pro"
    ollama_model: str = "llama2"
    ollama_base_url: str = "http://localhost:11434"

    # Database
    database_url: str = ""

    # Google Calendar
    google_calendar_credentials_path: str = "credentials.json"
    google_calendar_token_path: str = "token.json"

    # Garmin Connect
    garmin_email: str = ""
    garmin_password: str = ""

    # RAG Settings
    chromadb_path: str = "./chroma_db"
    embedding_model: str = "text-embedding-3-small"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow POSTGRES_* vars for docker-compose


def validate_api_keys(settings_obj: Settings) -> List[str]:
    """Validate that required API keys are configured."""
    missing_keys = []
    
    if settings_obj.llm_provider == "anthropic" and not settings_obj.anthropic_api_key:
        missing_keys.append("ANTHROPIC_API_KEY")
    elif settings_obj.llm_provider == "openai" and not settings_obj.openai_api_key:
        missing_keys.append("OPENAI_API_KEY")
    elif settings_obj.llm_provider == "gemini" and not settings_obj.google_api_key:
        missing_keys.append("GOOGLE_API_KEY")
    
    return missing_keys


settings = Settings()
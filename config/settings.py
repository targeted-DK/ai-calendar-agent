from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Provider
    llm_provider: Literal["anthropic", "openai", "gemini", "ollama"] = "anthropic"

    # API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

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

    # RAG Settings
    chromadb_path: str = "./chroma_db"
    embedding_model: str = "text-embedding-3-small"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

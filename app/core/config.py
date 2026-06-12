from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=False)

    # App
    app_name: str = "Research Copilot"
    app_version: str = "1.0.0"
    debug: bool = True

    # OpenAI (kept for future use)
    openai_api_key: str = "placeholder"
    openai_model: str = "gpt-4o-mini"

    # Groq
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    # Search
    tavily_api_key: str


@lru_cache()
def get_settings() -> Settings:
    return Settings()
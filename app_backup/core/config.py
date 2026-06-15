import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

load_dotenv(override=True)

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = "research-copilot"


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra="ignore")
    # App
    app_name: str = "Research Copilot"
    app_version: str = "1.0.0"
    debug: bool = True

    # Groq
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    # Search
    tavily_api_key: str


def get_settings() -> Settings:
    return Settings()
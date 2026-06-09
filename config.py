from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    llm_api_key: str
    llm_model: str = "gemini-2.0-flash"
    job_ttl_seconds: int = 3600
    session_ttl_seconds: int = 86400
    max_retries: int = 3
    relevance_threshold: float = 0.7
    confidence_threshold: float = 0.6

    class Config:
        env_file = ".env"


settings = Settings()

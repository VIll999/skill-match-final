from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://dev:dev@localhost:5442/skillmatch"
    )
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Skill-Match API"
    
    class Config:
        env_file = ".env"


settings = Settings()
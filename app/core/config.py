from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AssessorFinanceiro"
    environment: str = "development"
    database_url: str
    redis_url: str
    secret_key: str

    class Config:
        env_file = ".env"


settings = Settings()

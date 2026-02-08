from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AssessorFinanceiro"
    environment: str = "development"
    database_url: str
    redis_url: str
    secret_key: str
    access_token_expire_minutes: int = 60
    
    # Gmail OAuth settings (optional - can also use env vars directly)
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_project_id: str = ""
    gmail_redirect_uri: str = "https://web-production-6437a.up.railway.app/api/v1/gmail/callback"

    class Config:
        env_file = ".env"


settings = Settings()

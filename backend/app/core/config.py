from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "HR Copilot"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "mysql+pymysql://root:123456@localhost:3306/hr_copilot"
    SECRET_KEY: str = "hr-copilot-secret-key-for-jwt-token-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    UPLOAD_DIR: str = "uploads"

    class Config:
        case_sensitive = True


settings = Settings()
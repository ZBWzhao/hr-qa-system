from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "HR Copilot"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "mysql+pymysql://root:123456@localhost:3306/hr_copilot"
    SECRET_KEY: str = "hr-copilot-secret-key-for-jwt-token-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    UPLOAD_DIR: str = "uploads"

    # DeepSeek API配置
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Chroma向量数据库配置
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"

    # Embedding模型配置
    EMBEDDING_MODEL: str = "shibing624/text2vec-base-chinese"

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    ALLOWED_ORIGINS: str

    UPLOAD_DIR: str
    MAX_FILE_SIZE_MB: int

    EMAIL_USER: str
    EMAIL_PASSWORD: str
    EMAIL_HOST: str
    EMAIL_PORT: int

    GEMINI_API_KEY: str
    COHERE_API_KEY: str
    GROQ_API_KEY: str
    
    RAZORPAY_KEY_ID : str
    RAZORPAY_KEY_SECRET : str
    
    WEATHER_API_KEY : str
    
    CHAT_MEMORY_WINDOW : int
    
    KNOWLEDGE_BASE_DIR : str
    VECTOR_STORE_DIR : str

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def origins_list(self):
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def DATABASE_URL(self):
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=r"D:\FastAPI-Backend\.env")
    DB_USER: str = ""
    DB_PORT: str = ""
    DB_NAME: str = ""
    DB_PASS: str = ""
    DB_HOST: str = ""
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = ""
    GOOGLE_API_KEY: str = ""
    SECRET_KEY: str = ""
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_PORT: int = 587
    MAIL_SERVER: str = ""
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    
settings = Settings()
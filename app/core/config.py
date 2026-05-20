from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = 'postgresql+asyncpg://postgres:postgres@localhost:5432/task_manager'
    SECRET_KEY: str

    SMTP_HOST: str = 'smtp.yandex.ru'
    SMTP_PORT: int = 465
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM: str

    class Config:
        env_file = '.env'


settings = Settings()

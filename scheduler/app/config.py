from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "FairGPU Scheduler"
    environment: str = "development"
    heartbeat_interval: int = 10
    database_url: str

    class Config:
        env_file = ".env"

settings = Settings()
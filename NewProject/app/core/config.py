# my_fastapi_angular_backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SECRET_KEY: str = "lksnFSDkasndkls5932940hgno&7slanJSKDFN" # IMPORTANT: Change this for production!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "mysql+pymysql://staj_proje:Mnj09bnn3998AS+D@localhost:3306/fastapi_users_db"

    # This tells Pydantic Settings to load variables from a .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Create an instance of the Settings class.
# This 'settings' object is what other modules will import.
settings = Settings()
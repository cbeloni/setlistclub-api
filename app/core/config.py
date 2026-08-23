from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv(override=True)

# Nome e região do bucket fixos no código (Magalu Objects)
BUCKET_NAME = "cifras"
BUCKET_REGION = "br-se1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Setlist Club API"
    API_PREFIX: str = "/api/v1"
    BASE_URL: str = "http://localhost:3000"

    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DB: str = "setlistclub"
    MYSQL_USER: str = "setlistclub"
    MYSQL_PASSWORD: str = "setlistclub"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    BUCKET_URL: str = ""
    BUCKET_ACCESS_KEY_ID: str = ""
    BUCKET_SECRET_ACCESS_KEY: str = ""

    @property
    def bucket_endpoint(self) -> str | None:
        """Endpoint S3 da Magalu. Se BUCKET_URL não for definido, deriva por região."""
        if self.BUCKET_URL:
            return self.BUCKET_URL.rstrip("/")
        return f"https://{BUCKET_REGION}.magaluobjects.com"

    @property
    def bucket_configured(self) -> bool:
        return bool(
            self.bucket_endpoint
            and BUCKET_NAME
            and self.BUCKET_ACCESS_KEY_ID
            and self.BUCKET_SECRET_ACCESS_KEY
        )

    @property
    def bucket_base_url(self) -> str | None:
        """URL pública base para montar o caminho dos objetos no bucket (virtual-hosted)."""
        if not self.bucket_configured:
            return None
        return f"https://{BUCKET_NAME}.{BUCKET_REGION}.magaluobjects.com"

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()

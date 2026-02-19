# from pydantic_settings import BaseSettings, SettingsConfigDict
# from pydantic import Field

# class Settings(BaseSettings):
#     model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

#     app_name: str = Field(default="EdTech Autograder", alias="APP_NAME")
#     env: str = Field(default="dev", alias="ENV")
#     log_level: str = Field(default="INFO", alias="LOG_LEVEL")

#     database_url: str = Field(alias="DATABASE_URL")

#     redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
#     celery_broker_url: str = Field(default="", alias="CELERY_BROKER_URL")
#     celery_result_backend: str | None = Field(default=None, alias="CELERY_RESULT_BACKEND")

#     judge0_base_url: str = Field(default="https://judge0.example.com", alias="JUDGE0_BASE_URL")
#     judge0_api_key: str | None = Field(default=None, alias="JUDGE0_API_KEY")

# def get_settings() -> Settings:
#     s = Settings()
#     # If CELERY_BROKER_URL not explicitly set, fall back to REDIS_URL
#     if not s.celery_broker_url:
#         s.celery_broker_url = s.redis_url
#     return s

# from functools import lru_cache
# from pydantic import Field, AnyUrl
# from pydantic_settings import BaseSettings, SettingsConfigDict
# from typing import Optional


# class Settings(BaseSettings):
#     """
#     Central application configuration.

#     Loads values from:
#     - .env file
#     - Environment variables
#     """

#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_file_encoding="utf-8",
#         case_sensitive=False,
#         extra="ignore",
#     )

#     # -----------------------------
#     # Core Environment
#     # -----------------------------
#     env: str = Field(default="dev", alias="ENV")
#     log_level: str = Field(default="INFO", alias="LOG_LEVEL")

#     # -----------------------------
#     # Database
#     # -----------------------------
#     database_url: str = Field(..., alias="DATABASE_URL")

#     # -----------------------------
#     # Redis / Celery
#     # -----------------------------
#     redis_url: str = Field(..., alias="REDIS_URL")
#     celery_broker_url: Optional[str] = Field(default=None, alias="CELERY_BROKER_URL")
#     celery_result_backend: Optional[str] = Field(default=None, alias="CELERY_RESULT_BACKEND")

#     # -----------------------------
#     # Judge0 (for later tickets)
#     # -----------------------------
#     judge0_base_url: Optional[str] = Field(default=None, alias="JUDGE0_BASE_URL")
#     judge0_api_key: Optional[str] = Field(default=None, alias="JUDGE0_API_KEY")
    
#     # -----------------------------
#     # Post-processing / Validation
#     # -----------------------------
#     def model_post_init(self, __context):
#         """
#         Ensures Celery broker and backend default correctly.
#         """
#         if not self.celery_broker_url:
#             self.celery_broker_url = self.redis_url

#         if not self.celery_result_backend:
#             self.celery_result_backend = self.redis_url

#         if self.env not in ["dev", "staging", "prod"]:
#             raise ValueError("ENV must be one of: dev, staging, prod")

#         if self.log_level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
#             raise ValueError("Invalid LOG_LEVEL")


# @lru_cache
# def get_settings() -> Settings:
#     """
#     Cached settings instance to avoid reloading env repeatedly.
#     """
#     return Settings()

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core Environment
    app_name: str = Field(default="EdTech Autograder", alias="APP_NAME")
    env: str = Field(default="dev", alias="ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")

    # Redis / Celery
    redis_url: str = Field(..., alias="REDIS_URL")
    celery_broker_url: Optional[str] = Field(default=None, alias="CELERY_BROKER_URL")
    celery_result_backend: Optional[str] = Field(default=None, alias="CELERY_RESULT_BACKEND")

    # Judge0 (later)
    judge0_base_url: Optional[str] = Field(default=None, alias="JUDGE0_BASE_URL")
    judge0_api_key: Optional[str] = Field(default=None, alias="JUDGE0_API_KEY")

    # JWT / Auth
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")

    def model_post_init(self, __context):
        if not self.celery_broker_url:
            self.celery_broker_url = self.redis_url
        if not self.celery_result_backend:
            self.celery_result_backend = self.redis_url

        if self.env not in ["dev", "staging", "prod"]:
            raise ValueError("ENV must be one of: dev, staging, prod")

        if self.log_level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Invalid LOG_LEVEL")


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

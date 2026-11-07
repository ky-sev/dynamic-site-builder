from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Loads application configuration from environment variables and the local env file.
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / "frontend" / "env.local",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str | None = None
    pg_host: str | None = Field(default=None, validation_alias="PGHOST")
    pg_port: Annotated[int, Field(gt=0, le=65535)] = Field(
        default=5432, validation_alias="PGPORT"
    )
    pg_database: str | None = Field(default=None, validation_alias="PGDATABASE")
    pg_user: str | None = Field(default=None, validation_alias="PGUSER")
    pg_password: SecretStr | None = Field(default=None, validation_alias="PGPASSWORD")
    workflow_admin_token: SecretStr | None = None

    # Builds a SQLAlchemy-compatible database URL from the configured settings.
    def sqlalchemy_database_url(self) -> str:
        if self.database_url and self.database_url.strip():
            url = self.database_url.strip()
            if url.startswith("postgres://"):
                return "postgresql+psycopg://" + url.removeprefix("postgres://")
            if url.startswith("postgresql://"):
                return "postgresql+psycopg://" + url.removeprefix("postgresql://")
            return url

        if not self.pg_host or not self.pg_database or not self.pg_user:
            raise RuntimeError(
                "Set DATABASE_URL or configure PGHOST, PGDATABASE, and PGUSER."
            )

        return URL.create(
            "postgresql+psycopg",
            username=self.pg_user,
            password=(
                self.pg_password.get_secret_value() if self.pg_password else None
            ),
            host=self.pg_host,
            port=self.pg_port,
            database=self.pg_database,
        ).render_as_string(hide_password=False)


settings = Settings()

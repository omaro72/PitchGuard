from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import (
    AnyHttpUrl,
    Field,
    StringConstraints,
    TypeAdapter,
    ValidationError,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
HTTP_URL_ADAPTER = TypeAdapter(AnyHttpUrl)
OllamaModelName = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9._:/-]+$",
        strip_whitespace=True,
    ),
]


class AppEnvironment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"


def normalize_http_url(value: str, variable_name: str, origin_only: bool) -> str:
    stripped_value = value.strip()
    try:
        parsed_url = HTTP_URL_ADAPTER.validate_python(stripped_value)
    except ValidationError as error:
        raise ValueError(f"{variable_name} must be a valid HTTP or HTTPS URL") from error

    if parsed_url.username is not None or parsed_url.password is not None:
        raise ValueError(f"{variable_name} must not contain credentials")
    if parsed_url.query is not None:
        raise ValueError(f"{variable_name} must not contain query parameters")
    if parsed_url.fragment is not None:
        raise ValueError(f"{variable_name} must not contain a fragment")
    if origin_only and parsed_url.path not in (None, "", "/"):
        raise ValueError(f"{variable_name} must be an origin without an application path")

    return str(parsed_url).rstrip("/")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
    )

    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: OllamaModelName = "qwen3:4b"
    ollama_timeout_seconds: int = Field(default=120, ge=1, le=600)
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        min_length=1,
        max_length=10,
    )

    @field_validator("ollama_base_url", mode="before")
    @classmethod
    def validate_ollama_base_url(cls, value: str) -> str:
        return normalize_http_url(value, "OLLAMA_BASE_URL", origin_only=False)

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, origins: list[str]) -> list[str]:
        normalized_origins = [
            normalize_http_url(origin, "CORS_ORIGINS", origin_only=True) for origin in origins
        ]
        if len(normalized_origins) != len(set(normalized_origins)):
            raise ValueError("CORS_ORIGINS must not contain duplicates")
        return normalized_origins


@lru_cache
def get_settings() -> Settings:
    return Settings(_env_file=BACKEND_ENV_FILE)

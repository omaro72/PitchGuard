import asyncio
from pathlib import Path

import httpx2
import pytest
from fastapi import FastAPI
from pydantic import ValidationError

from app import config
from app.config import AppEnvironment, Settings, get_settings
from app.main import create_app

ENVIRONMENT_VARIABLES = (
    "APP_ENV",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
    "OLLAMA_TIMEOUT_SECONDS",
    "CORS_ORIGINS",
)


@pytest.fixture(autouse=True)
def isolate_settings(monkeypatch: pytest.MonkeyPatch):
    for variable in ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(variable, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def settings_without_env_file(**values: object) -> Settings:
    return Settings(_env_file=None, **values)


def test_defaults_are_safe_for_local_development() -> None:
    settings = settings_without_env_file()

    assert settings.app_env is AppEnvironment.DEVELOPMENT
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.ollama_model == "qwen3:8b"
    assert settings.ollama_timeout_seconds == 120
    assert settings.cors_origins == ["http://localhost:3000"]


def test_environment_variables_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("OLLAMA_BASE_URL", " https://ollama.example.com/service/ ")
    monkeypatch.setenv("OLLAMA_MODEL", " library/model-name_1.2:latest ")
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv(
        "CORS_ORIGINS",
        '[" http://localhost:3001/ ", "https://preview.example.com/"]',
    )

    settings = settings_without_env_file()

    assert settings.app_env is AppEnvironment.TEST
    assert settings.ollama_base_url == "https://ollama.example.com/service"
    assert settings.ollama_model == "library/model-name_1.2:latest"
    assert settings.ollama_timeout_seconds == 45
    assert settings.cors_origins == [
        "http://localhost:3001",
        "https://preview.example.com",
    ]


@pytest.mark.parametrize("app_env", ["production", "staging", "local"])
def test_unknown_application_environment_is_rejected(app_env: str) -> None:
    with pytest.raises(ValidationError):
        settings_without_env_file(app_env=app_env)


@pytest.mark.parametrize(
    "url",
    [
        "not-a-url",
        "ftp://localhost:11434",
        "http://user:password@localhost:11434",
        "http://localhost:11434?debug=true",
        "http://localhost:11434#models",
    ],
)
def test_invalid_ollama_url_is_rejected(url: str) -> None:
    with pytest.raises(ValidationError):
        settings_without_env_file(ollama_base_url=url)


@pytest.mark.parametrize(
    "model_name",
    ["", "   ", "model name", "model@latest", "model\\name"],
)
def test_invalid_ollama_model_is_rejected(model_name: str) -> None:
    with pytest.raises(ValidationError):
        settings_without_env_file(ollama_model=model_name)


def test_ollama_model_over_maximum_length_is_rejected() -> None:
    with pytest.raises(ValidationError):
        settings_without_env_file(ollama_model="m" * 101)


@pytest.mark.parametrize("timeout", [0, -1, 601, "not-a-number"])
def test_invalid_ollama_timeout_is_rejected(timeout: object) -> None:
    with pytest.raises(ValidationError):
        settings_without_env_file(ollama_timeout_seconds=timeout)


@pytest.mark.parametrize("timeout", [1, 600])
def test_ollama_timeout_boundaries_are_accepted(timeout: int) -> None:
    settings = settings_without_env_file(ollama_timeout_seconds=timeout)

    assert settings.ollama_timeout_seconds == timeout


@pytest.mark.parametrize(
    "origin",
    [
        "not-a-url",
        "*",
        "ftp://localhost:3000",
        "http://user:password@localhost:3000",
        "http://localhost:3000?preview=true",
        "http://localhost:3000#preview",
        "http://localhost:3000/application",
    ],
)
def test_invalid_cors_origin_is_rejected(origin: str) -> None:
    with pytest.raises(ValidationError):
        settings_without_env_file(cors_origins=[origin])


def test_duplicate_cors_origins_are_rejected_after_normalization() -> None:
    with pytest.raises(ValidationError):
        settings_without_env_file(
            cors_origins=["http://localhost:3000", "http://localhost:3000/"],
        )


def test_empty_cors_origin_list_is_rejected() -> None:
    with pytest.raises(ValidationError):
        settings_without_env_file(cors_origins=[])


def test_more_than_ten_cors_origins_are_rejected() -> None:
    origins = [f"https://preview{index}.example.com" for index in range(11)]

    with pytest.raises(ValidationError):
        settings_without_env_file(cors_origins=origins)


def test_backend_environment_example_loads_successfully() -> None:
    example_path = Path(__file__).resolve().parents[1] / ".env.example"

    settings = Settings(_env_file=example_path)

    assert settings == settings_without_env_file()


def test_environment_variable_takes_precedence_over_environment_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    environment_file = tmp_path / ".env"
    environment_file.write_text("OLLAMA_MODEL=file-model\n", encoding="utf-8")
    monkeypatch.setenv("OLLAMA_MODEL", "environment-model")

    settings = Settings(_env_file=environment_file)

    assert settings.ollama_model == "environment-model"


def test_environment_file_names_are_case_insensitive(tmp_path: Path) -> None:
    environment_file = tmp_path / ".env"
    environment_file.write_text("app_env=test\n", encoding="utf-8")

    settings = Settings(_env_file=environment_file)

    assert settings.app_env is AppEnvironment.TEST


def test_unexpected_environment_file_property_is_rejected(tmp_path: Path) -> None:
    environment_file = tmp_path / ".env"
    environment_file.write_text("UNEXPECTED_SETTING=value\n", encoding="utf-8")

    with pytest.raises(ValidationError):
        Settings(_env_file=environment_file)


def test_get_settings_caches_until_cleared(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(config, "BACKEND_ENV_FILE", tmp_path / "missing.env")

    first = get_settings()
    monkeypatch.setenv("OLLAMA_MODEL", "changed-model")
    second = get_settings()

    assert second is first
    assert second.ollama_model == "qwen3:8b"

    get_settings.cache_clear()
    third = get_settings()

    assert third is not first
    assert third.ollama_model == "changed-model"


async def request_with_origin(app: FastAPI, origin: str) -> httpx2.Response:
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get("/api/health", headers={"Origin": origin})


async def request_preflight(app: FastAPI, method: str) -> httpx2.Response:
    transport = httpx2.ASGITransport(app=app)
    headers = {
        "Origin": "http://localhost:3001",
        "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": "Content-Type",
    }
    async with httpx2.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.options("/api/health", headers=headers)


def test_fastapi_uses_only_the_configured_cors_origins() -> None:
    settings = settings_without_env_file(cors_origins=["http://localhost:3001"])
    application = create_app(settings)

    allowed_response = asyncio.run(request_with_origin(application, "http://localhost:3001"))
    denied_response = asyncio.run(request_with_origin(application, "http://localhost:3000"))

    assert allowed_response.headers["access-control-allow-origin"] == "http://localhost:3001"
    assert "access-control-allow-credentials" not in allowed_response.headers
    assert "access-control-allow-origin" not in denied_response.headers


def test_fastapi_cors_allows_only_the_provisional_request_shape() -> None:
    settings = settings_without_env_file(cors_origins=["http://localhost:3001"])
    application = create_app(settings)

    accepted_response = asyncio.run(request_preflight(application, "POST"))
    rejected_response = asyncio.run(request_preflight(application, "DELETE"))

    assert accepted_response.status_code == 200
    assert "POST" in accepted_response.headers["access-control-allow-methods"]
    assert "content-type" in accepted_response.headers["access-control-allow-headers"].lower()
    assert rejected_response.status_code == 400


def test_application_creation_fails_for_invalid_configuration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(config, "BACKEND_ENV_FILE", tmp_path / "missing.env")
    monkeypatch.setenv("OLLAMA_MODEL", "invalid model")
    get_settings.cache_clear()

    with pytest.raises(ValidationError):
        create_app()

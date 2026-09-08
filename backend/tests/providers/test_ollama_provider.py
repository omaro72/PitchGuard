import asyncio
import json
from unittest.mock import AsyncMock, Mock

import httpx
import ollama
import pytest
from pydantic import BaseModel, Field, ValidationError

import app.providers.ollama as ollama_provider_module
from app.config import Settings
from app.providers import (
    GenerationOptions,
    OllamaProvider,
    ProviderConnectionError,
    ProviderModelNotFoundError,
    ProviderOutputValidationError,
    ProviderResponseError,
    ProviderTimeoutError,
)
from app.schemas import EvidenceReview


class ExampleStructuredOutput(BaseModel):
    answer: str
    score: int


class LengthBoundedStructuredOutput(BaseModel):
    answer: str = Field(min_length=1, max_length=2_000)


def settings(**values: object) -> Settings:
    return Settings(_env_file=None, **values)


def client_response(content: str | None) -> ollama.ChatResponse:
    return ollama.ChatResponse(
        message=ollama.Message(role="assistant", content=content),
    )


def injected_client(content: str | None = '{"answer":"ok","score":10}') -> AsyncMock:
    client = AsyncMock(spec=ollama.AsyncClient)
    client.chat.return_value = client_response(content)
    return client


def generate(
    provider: OllamaProvider,
    *,
    system_prompt: str = "Return the requested fictional result.",
    user_prompt: str = "Evaluate the fictional example.",
    options: GenerationOptions | None = None,
) -> ExampleStructuredOutput:
    return asyncio.run(
        provider.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=ExampleStructuredOutput,
            options=options,
        )
    )


def test_valid_response_returns_requested_pydantic_model() -> None:
    client = injected_client()
    provider = OllamaProvider(settings(), client=client)

    result = generate(provider)

    assert isinstance(result, ExampleStructuredOutput)
    assert result == ExampleStructuredOutput(answer="ok", score=10)


def test_default_request_uses_structured_non_streaming_options() -> None:
    client = injected_client()
    provider = OllamaProvider(settings(ollama_model="library/model:latest"), client=client)

    generate(provider, system_prompt="System instructions", user_prompt="User input")

    client.chat.assert_awaited_once_with(
        model="library/model:latest",
        messages=[
            {"role": "system", "content": "System instructions"},
            {"role": "user", "content": "User input"},
        ],
        stream=False,
        think=False,
        format=ExampleStructuredOutput.model_json_schema(),
        options={"temperature": 0.0, "num_predict": 2_048},
    )


def test_custom_generation_options_are_translated_for_ollama() -> None:
    client = injected_client()
    provider = OllamaProvider(settings(), client=client)
    options = GenerationOptions(temperature=0.75, max_output_tokens=4_096)

    generate(provider, options=options)

    assert client.chat.await_args.kwargs["options"] == {
        "temperature": 0.75,
        "num_predict": 4_096,
    }


def test_ollama_schema_omits_string_maximums_that_break_grammar_parsing() -> None:
    client = injected_client('{"claims":[],"summary":"ok","missing_context":[]}')
    provider = OllamaProvider(settings(), client=client)

    result = asyncio.run(
        provider.generate_structured(
            system_prompt="Return the requested fictional result.",
            user_prompt="Evaluate the fictional example.",
            response_model=EvidenceReview,
        )
    )

    schema = client.chat.await_args.kwargs["format"]
    serialized_schema = json.dumps(schema)
    assert '"maxLength"' not in serialized_schema
    assert '"minLength"' in serialized_schema
    assert result.summary == "ok"


def test_omitted_ollama_maximum_remains_enforced_after_generation() -> None:
    content = '{"answer":"' + "x" * 2_001 + '"}'
    client = injected_client(content)
    provider = OllamaProvider(settings(), client=client)

    with pytest.raises(ProviderOutputValidationError):
        asyncio.run(
            provider.generate_structured(
                system_prompt="Return the requested fictional result.",
                user_prompt="Evaluate the fictional example.",
                response_model=LengthBoundedStructuredOutput,
            )
        )


def test_production_client_uses_configured_host_and_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = injected_client()
    constructor = Mock(return_value=client)
    monkeypatch.setattr(ollama_provider_module.ollama, "AsyncClient", constructor)

    provider = OllamaProvider(
        settings(
            ollama_base_url="https://ollama.example.com/service",
            ollama_timeout_seconds=45,
        )
    )

    constructor.assert_called_once_with(
        host="https://ollama.example.com/service",
        timeout=45,
    )
    asyncio.run(provider.close())


def test_provider_module_has_no_global_client() -> None:
    global_clients = [
        value
        for value in vars(ollama_provider_module).values()
        if isinstance(value, ollama.AsyncClient)
    ]

    assert global_clients == []


@pytest.mark.parametrize(
    ("system_prompt", "user_prompt", "field_name"),
    [
        ("", "Valid user input", "system_prompt"),
        ("   ", "Valid user input", "system_prompt"),
        ("Valid system instructions", "", "user_prompt"),
        ("Valid system instructions", "   ", "user_prompt"),
    ],
)
def test_blank_prompt_is_rejected_before_client_call(
    system_prompt: str,
    user_prompt: str,
    field_name: str,
) -> None:
    client = injected_client()
    provider = OllamaProvider(settings(), client=client)

    with pytest.raises(ValueError, match=field_name):
        generate(provider, system_prompt=system_prompt, user_prompt=user_prompt)

    client.chat.assert_not_awaited()


@pytest.mark.parametrize(
    "values",
    [
        {"temperature": -0.01},
        {"temperature": 2.01},
        {"max_output_tokens": 0},
        {"max_output_tokens": -1},
        {"max_output_tokens": 32_769},
    ],
)
def test_invalid_generation_options_are_rejected(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        GenerationOptions.model_validate(values)


def test_generation_options_are_immutable() -> None:
    options = GenerationOptions()

    with pytest.raises(ValidationError):
        options.temperature = 1.0


@pytest.mark.parametrize("content", [None, "", "   "])
def test_empty_response_content_is_rejected(content: str | None) -> None:
    provider = OllamaProvider(settings(), client=injected_client(content))

    with pytest.raises(ProviderOutputValidationError) as captured:
        generate(provider)

    assert captured.value.code == "provider_output_validation_error"
    assert captured.value.retryable is True
    assert str(captured.value) == "The AI returned an invalid response."


def test_malformed_json_is_rejected_without_leaking_content() -> None:
    content = "confidential-raw-output is not JSON"
    provider = OllamaProvider(settings(), client=injected_client(content))

    with pytest.raises(ProviderOutputValidationError) as captured:
        generate(
            provider,
            system_prompt="confidential-system-prompt",
            user_prompt="confidential-user-prompt",
        )

    error_text = str(captured.value)
    assert content not in error_text
    assert "confidential-system-prompt" not in error_text
    assert "confidential-user-prompt" not in error_text
    assert isinstance(captured.value.__cause__, ValidationError)


@pytest.mark.parametrize(
    "content",
    [
        '{"answer":"ok"}',
        '{"answer":"ok","score":"not-a-number"}',
    ],
)
def test_schema_invalid_json_is_rejected_without_leaking_content(content: str) -> None:
    provider = OllamaProvider(settings(), client=injected_client(content))

    with pytest.raises(ProviderOutputValidationError) as captured:
        generate(
            provider,
            system_prompt="confidential-system-prompt",
            user_prompt="confidential-user-prompt",
        )

    error_text = str(captured.value)
    assert content not in error_text
    assert "confidential-system-prompt" not in error_text
    assert "confidential-user-prompt" not in error_text
    assert isinstance(captured.value.__cause__, ValidationError)


@pytest.mark.parametrize(
    "original_error",
    [
        ConnectionError("confidential-connection-detail"),
        httpx.ConnectError(
            "confidential-connection-detail",
            request=httpx.Request("POST", "http://localhost:11434/api/chat"),
        ),
    ],
)
def test_connection_failure_is_mapped_and_chained_without_leaking_details(
    original_error: Exception,
) -> None:
    client = injected_client()
    client.chat.side_effect = original_error
    provider = OllamaProvider(settings(), client=client)

    with pytest.raises(ProviderConnectionError) as captured:
        generate(provider)

    assert captured.value.code == "provider_connection_error"
    assert captured.value.retryable is True
    assert captured.value.status_code is None
    assert captured.value.__cause__ is original_error
    assert "confidential-connection-detail" not in str(captured.value)
    assert str(captured.value) == "The local AI service is unavailable."


def test_timeout_is_mapped_and_chained() -> None:
    client = injected_client()
    original_error = httpx.ReadTimeout(
        "confidential-timeout-detail",
        request=httpx.Request("POST", "http://localhost:11434/api/chat"),
    )
    client.chat.side_effect = original_error
    provider = OllamaProvider(settings(), client=client)

    with pytest.raises(ProviderTimeoutError) as captured:
        generate(provider)

    assert captured.value.code == "provider_timeout_error"
    assert captured.value.retryable is True
    assert captured.value.__cause__ is original_error
    assert "confidential-timeout-detail" not in str(captured.value)
    assert str(captured.value) == "The local AI service timed out."


def test_model_not_found_is_non_retryable_and_does_not_expose_configuration() -> None:
    client = injected_client()
    original_error = ollama.ResponseError("confidential-response-body", status_code=404)
    client.chat.side_effect = original_error
    provider = OllamaProvider(settings(ollama_model="example/model:latest"), client=client)

    with pytest.raises(ProviderModelNotFoundError) as captured:
        generate(provider)

    assert captured.value.code == "provider_model_not_found_error"
    assert captured.value.retryable is False
    assert captured.value.status_code == 404
    assert captured.value.__cause__ is original_error
    assert str(captured.value) == "The configured local AI model is unavailable."
    assert "example/model:latest" not in str(captured.value)
    assert "confidential-response-body" not in str(captured.value)


def test_server_error_preserves_status_without_leaking_response() -> None:
    client = injected_client()
    original_error = ollama.ResponseError("confidential-response-body", status_code=503)
    client.chat.side_effect = original_error
    provider = OllamaProvider(settings(), client=client)

    with pytest.raises(ProviderResponseError) as captured:
        generate(provider)

    assert captured.value.code == "provider_response_error"
    assert captured.value.retryable is True
    assert captured.value.status_code == 503
    assert captured.value.__cause__ is original_error
    assert "confidential-response-body" not in str(captured.value)
    assert str(captured.value) == "The local AI service returned an error."


def test_response_failure_without_status_is_mapped_safely() -> None:
    client = injected_client()
    original_error = ollama.ResponseError("confidential-response-body", status_code=0)
    client.chat.side_effect = original_error
    provider = OllamaProvider(settings(), client=client)

    with pytest.raises(ProviderResponseError) as captured:
        generate(provider)

    assert captured.value.status_code is None
    assert captured.value.retryable is True
    assert captured.value.__cause__ is original_error
    assert "confidential-response-body" not in str(captured.value)


def test_owned_client_is_closed_once(monkeypatch: pytest.MonkeyPatch) -> None:
    client = injected_client()
    monkeypatch.setattr(ollama_provider_module.ollama, "AsyncClient", Mock(return_value=client))
    provider = OllamaProvider(settings())

    asyncio.run(provider.close())
    asyncio.run(provider.close())

    client.close.assert_awaited_once_with()


def test_injected_client_is_not_closed() -> None:
    client = injected_client()
    provider = OllamaProvider(settings(), client=client)

    asyncio.run(provider.close())

    client.close.assert_not_awaited()

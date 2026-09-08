import httpx
import ollama
from pydantic import ValidationError

from app.config import Settings
from app.providers.base import GenerationOptions, ResponseModelT
from app.providers.errors import (
    ProviderConnectionError,
    ProviderModelNotFoundError,
    ProviderOutputValidationError,
    ProviderResponseError,
    ProviderTimeoutError,
)


def _ollama_compatible_schema(response_model: type[ResponseModelT]) -> dict[str, object]:
    schema = response_model.model_json_schema()
    pending: list[object] = [schema]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            value.pop("maxLength", None)
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    return schema


class OllamaProvider:
    def __init__(
        self,
        settings: Settings,
        client: ollama.AsyncClient | None = None,
    ) -> None:
        self._model = settings.ollama_model
        self._owns_client = client is None
        self._client = (
            client
            if client is not None
            else ollama.AsyncClient(
                host=settings.ollama_base_url,
                timeout=settings.ollama_timeout_seconds,
            )
        )
        self._closed = False

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseModelT],
        options: GenerationOptions | None = None,
    ) -> ResponseModelT:
        if not system_prompt.strip():
            raise ValueError("system_prompt must not be blank")
        if not user_prompt.strip():
            raise ValueError("user_prompt must not be blank")

        generation_options = options or GenerationOptions()
        try:
            response = await self._client.chat(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                stream=False,
                think=False,
                format=_ollama_compatible_schema(response_model),
                options={
                    "temperature": generation_options.temperature,
                    "num_predict": generation_options.max_output_tokens,
                },
            )
        except httpx.TimeoutException as error:
            raise ProviderTimeoutError() from error
        except (ConnectionError, httpx.ConnectError) as error:
            raise ProviderConnectionError() from error
        except ollama.ResponseError as error:
            status_code = error.status_code if error.status_code >= 100 else None
            if status_code == 404:
                raise ProviderModelNotFoundError(status_code) from error
            raise ProviderResponseError(status_code) from error

        content = response.message.content
        if not isinstance(content, str) or not content.strip():
            raise ProviderOutputValidationError()

        try:
            return response_model.model_validate_json(content)
        except ValidationError as error:
            raise ProviderOutputValidationError() from error

    async def close(self) -> None:
        if not self._owns_client or self._closed:
            return
        await self._client.close()
        self._closed = True

class ProviderError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str,
        retryable: bool,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.retryable = retryable
        self.status_code = status_code


class ProviderConnectionError(ProviderError):
    def __init__(self) -> None:
        super().__init__(
            "Could not connect to Ollama. Confirm the local service is running and reachable.",
            code="provider_connection_error",
            retryable=True,
        )


class ProviderTimeoutError(ProviderError):
    def __init__(self) -> None:
        super().__init__(
            "Ollama did not respond before the configured timeout.",
            code="provider_timeout_error",
            retryable=True,
        )


class ProviderModelNotFoundError(ProviderError):
    def __init__(self, model: str, status_code: int = 404) -> None:
        super().__init__(
            f"The configured Ollama model is unavailable. Run `ollama pull {model}` to install it.",
            code="provider_model_not_found_error",
            retryable=False,
            status_code=status_code,
        )


class ProviderResponseError(ProviderError):
    def __init__(self, status_code: int | None = None) -> None:
        status_detail = f" with HTTP status {status_code}" if status_code is not None else ""
        retryable = status_code is None or status_code == 429 or status_code >= 500
        super().__init__(
            f"Ollama returned an unsuccessful response{status_detail}.",
            code="provider_response_error",
            retryable=retryable,
            status_code=status_code,
        )


class ProviderOutputValidationError(ProviderError):
    def __init__(self) -> None:
        super().__init__(
            "Ollama returned empty or invalid structured output.",
            code="provider_output_validation_error",
            retryable=True,
        )

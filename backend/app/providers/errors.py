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
            "The local AI service is unavailable.",
            code="provider_connection_error",
            retryable=True,
        )


class ProviderTimeoutError(ProviderError):
    def __init__(self) -> None:
        super().__init__(
            "The local AI service timed out.",
            code="provider_timeout_error",
            retryable=True,
        )


class ProviderModelNotFoundError(ProviderError):
    def __init__(self, status_code: int = 404) -> None:
        super().__init__(
            "The configured local AI model is unavailable.",
            code="provider_model_not_found_error",
            retryable=False,
            status_code=status_code,
        )


class ProviderResponseError(ProviderError):
    def __init__(self, status_code: int | None = None) -> None:
        retryable = status_code is None or status_code == 429 or status_code >= 500
        super().__init__(
            "The local AI service returned an error.",
            code="provider_response_error",
            retryable=retryable,
            status_code=status_code,
        )


class ProviderOutputValidationError(ProviderError):
    def __init__(self) -> None:
        super().__init__(
            "The AI returned an invalid response.",
            code="provider_output_validation_error",
            retryable=True,
        )

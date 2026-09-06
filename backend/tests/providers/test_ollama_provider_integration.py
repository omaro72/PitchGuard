import asyncio
import os

import pytest
from pydantic import BaseModel

from app.config import get_settings
from app.providers import GenerationOptions, OllamaProvider


class IntegrationStructuredOutput(BaseModel):
    answer: str


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_OLLAMA_INTEGRATION") != "1",
    reason="Set RUN_OLLAMA_INTEGRATION=1 to contact the configured local Ollama service",
)
def test_local_ollama_structured_generation() -> None:
    async def run() -> IntegrationStructuredOutput:
        provider = OllamaProvider(get_settings())
        try:
            return await provider.generate_structured(
                system_prompt="Return a minimal JSON response matching the supplied schema.",
                user_prompt='Return the fictional answer "ok".',
                response_model=IntegrationStructuredOutput,
                options=GenerationOptions(max_output_tokens=64),
            )
        finally:
            await provider.close()

    result = asyncio.run(run())

    assert isinstance(result, IntegrationStructuredOutput)

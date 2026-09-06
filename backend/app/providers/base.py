from typing import Protocol, TypeVar

from pydantic import BaseModel, ConfigDict, Field

ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


class GenerationOptions(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=2_048, ge=1, le=32_768)


class StructuredGenerationProvider(Protocol):
    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseModelT],
        options: GenerationOptions | None = None,
    ) -> ResponseModelT: ...

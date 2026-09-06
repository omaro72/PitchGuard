from dataclasses import dataclass
from typing import cast

import pytest
from pydantic import BaseModel

from app.providers.base import GenerationOptions, ResponseModelT
from app.schemas import ReviewRequest


@dataclass(frozen=True, slots=True)
class ProviderCall:
    system_prompt: str
    user_prompt: str
    response_model: type[BaseModel]
    options: GenerationOptions | None


class RecordingProvider:
    def __init__(
        self,
        result: BaseModel | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.calls: list[ProviderCall] = []

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ResponseModelT],
        options: GenerationOptions | None = None,
    ) -> ResponseModelT:
        self.calls.append(
            ProviderCall(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=response_model,
                options=options,
            )
        )
        if self.error is not None:
            raise self.error
        if self.result is None or not isinstance(self.result, response_model):
            raise AssertionError("The recording provider needs a matching configured result")
        return cast(ResponseModelT, self.result)


@pytest.fixture
def review_request() -> ReviewRequest:
    return ReviewRequest.model_validate(
        {
            "campaign": {
                "company_name": "Fictional Research",
                "announcement": "A fictional workplace productivity study is being published.",
                "target_audience": "Workplace technology readers",
            },
            "evidence": [
                {
                    "id": "E1",
                    "source": "Fictional internal study",
                    "content": "A study of 120 users found 22% less administrative time.",
                    "confidential": False,
                },
                {
                    "id": "E2",
                    "source": "Fictional launch plan",
                    "content": "The fictional launch date is 15 October 2026.",
                    "confidential": True,
                },
            ],
            "journalist": {
                "name": "Alex Morgan",
                "publication": "Example News",
                "beat": "Workplace technology and privacy",
                "recent_coverage": [
                    {
                        "id": "C1",
                        "title": "Privacy in workplace software",
                        "summary": "A fictional article about privacy controls in workplace tools.",
                        "publication_date": "2026-09-01",
                        "url": "https://example.com/workplace-privacy",
                    }
                ],
            },
            "pitch": (
                "Hello Alex,\nOur customers save 22% of administrative time. "
                "The confidential launch date is 15 October 2026. "
                "Would you like the fictional report?"
            ),
        }
    )

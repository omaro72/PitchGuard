import asyncio
from collections.abc import Sequence

import pytest

from app.schemas import EvidenceReview, RelevanceReview, ReviewRequest, RiskReview


class FakeReviewer[ReviewerResultT]:
    def __init__(
        self,
        outcomes: Sequence[ReviewerResultT | Exception],
        *,
        delay_seconds: float = 0,
        finish_gate: asyncio.Event | None = None,
    ) -> None:
        if not outcomes:
            raise ValueError("At least one fake reviewer outcome is required")
        self._outcomes = outcomes
        self._delay_seconds = delay_seconds
        self._finish_gate = finish_gate
        self.call_count = 0
        self.cancelled_count = 0
        self.requests: list[ReviewRequest] = []
        self.started = asyncio.Event()
        self.finished = asyncio.Event()

    async def review(self, request: ReviewRequest) -> ReviewerResultT:
        self.call_count += 1
        self.requests.append(request)
        self.started.set()
        try:
            if self._delay_seconds:
                await asyncio.sleep(self._delay_seconds)
            if self._finish_gate is not None:
                await self._finish_gate.wait()
            outcome = self._outcomes[min(self.call_count - 1, len(self._outcomes) - 1)]
            if isinstance(outcome, Exception):
                raise outcome
            return outcome
        except asyncio.CancelledError:
            self.cancelled_count += 1
            raise
        finally:
            self.finished.set()


@pytest.fixture
def review_request() -> ReviewRequest:
    return ReviewRequest.model_validate(
        {
            "campaign": {
                "company_name": "Fictional Research",
                "announcement": "A fictional workplace study is ready for publication.",
                "target_audience": "Workplace technology readers",
            },
            "evidence": [
                {
                    "id": "E1",
                    "source": "Fictional internal study",
                    "content": "A study of 120 users found 22% less administrative time.",
                }
            ],
            "journalist": {
                "name": "Alex Morgan",
                "publication": "Example News",
                "beat": "Workplace technology and privacy",
                "recent_coverage": [
                    {
                        "id": "C1",
                        "title": "Privacy in workplace software",
                        "summary": "A fictional article about privacy in workplace tools.",
                    }
                ],
            },
            "pitch": (
                "Hello Alex, our study found 22% less administrative time. "
                "Would you like the fictional report?"
            ),
        }
    )


@pytest.fixture
def evidence_review() -> EvidenceReview:
    return EvidenceReview(
        claims=[],
        summary="The supplied claims were reviewed against the fictional evidence.",
        missing_context=[],
    )


@pytest.fixture
def relevance_review() -> RelevanceReview:
    return RelevanceReview(
        relevance_score=84,
        personalization_score=71,
        summary="The fictional pitch matches the supplied journalist profile.",
        matched_topics=["workplace technology"],
        mismatches=[],
        missing_context=[],
    )


@pytest.fixture
def risk_review() -> RiskReview:
    return RiskReview(
        findings=[],
        summary="No language risks were found in the fictional pitch.",
        missing_context=[],
    )

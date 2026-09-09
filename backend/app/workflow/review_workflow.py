import asyncio
from collections.abc import Awaitable, Callable
from typing import Protocol

from app.providers.errors import ProviderError
from app.reviewers.errors import ReviewerContractError
from app.schemas import (
    EvidenceReview,
    RelevanceReview,
    ReviewerError,
    ReviewerName,
    ReviewRequest,
    RiskReview,
)
from app.workflow.models import ReviewWorkflowResult
from app.workflow.policy import ReviewWorkflowPolicy

type ReviewerResult = EvidenceReview | RelevanceReview | RiskReview
type ReviewerOutcome = ReviewerResult | ReviewerError
type ReviewerCall = Callable[[], Awaitable[ReviewerResult]]


class _EvidenceReviewer(Protocol):
    async def review(self, request: ReviewRequest) -> EvidenceReview: ...


class _RelevanceReviewer(Protocol):
    async def review(self, request: ReviewRequest) -> RelevanceReview: ...


class _RiskReviewer(Protocol):
    async def review(self, request: ReviewRequest) -> RiskReview: ...


class ReviewWorkflow:
    _reviewer_order = (
        ReviewerName.EVIDENCE,
        ReviewerName.RELEVANCE,
        ReviewerName.RISK,
    )

    def __init__(
        self,
        evidence_reviewer: _EvidenceReviewer,
        relevance_reviewer: _RelevanceReviewer,
        risk_reviewer: _RiskReviewer,
        policy: ReviewWorkflowPolicy | None = None,
    ) -> None:
        self._evidence_reviewer = evidence_reviewer
        self._relevance_reviewer = relevance_reviewer
        self._risk_reviewer = risk_reviewer
        self._policy = policy or ReviewWorkflowPolicy()

    async def run(self, request: ReviewRequest) -> ReviewWorkflowResult:
        reviewer_calls: dict[ReviewerName, ReviewerCall] = {
            ReviewerName.EVIDENCE: lambda: self._evidence_reviewer.review(request),
            ReviewerName.RELEVANCE: lambda: self._relevance_reviewer.review(request),
            ReviewerName.RISK: lambda: self._risk_reviewer.review(request),
        }
        outcomes: dict[ReviewerName, ReviewerOutcome] = {}
        for reviewer in self._reviewer_order:
            outcomes[reviewer] = await self._run_reviewer(
                reviewer,
                reviewer_calls[reviewer],
            )
        return self._build_result(outcomes)

    async def _run_reviewer(
        self,
        reviewer: ReviewerName,
        reviewer_call: ReviewerCall,
    ) -> ReviewerOutcome:
        for attempt_number in range(1, self._policy.max_attempts + 1):
            try:
                async with asyncio.timeout(self._policy.attempt_timeout_seconds):
                    return await reviewer_call()
            except TimeoutError:
                final_error = ReviewerError(
                    reviewer=reviewer,
                    code="workflow_attempt_timeout",
                    message=(
                        f"The {reviewer.value.lower()} reviewer exceeded the workflow "
                        "attempt timeout."
                    ),
                    retryable=True,
                )
            except (ProviderError, ReviewerContractError) as error:
                final_error = ReviewerError(
                    reviewer=reviewer,
                    code=error.code,
                    message=error.message,
                    retryable=error.retryable,
                )

            if not final_error.retryable or attempt_number == self._policy.max_attempts:
                return final_error
            await asyncio.sleep(self._policy.retry_delay_seconds)

        raise AssertionError("The workflow attempt loop ended without an outcome")

    def _build_result(
        self,
        outcomes: dict[ReviewerName, ReviewerOutcome],
    ) -> ReviewWorkflowResult:
        evidence_outcome = outcomes[ReviewerName.EVIDENCE]
        relevance_outcome = outcomes[ReviewerName.RELEVANCE]
        risk_outcome = outcomes[ReviewerName.RISK]

        if not isinstance(evidence_outcome, (EvidenceReview, ReviewerError)):
            raise TypeError("The evidence reviewer returned an unexpected result type")
        if not isinstance(relevance_outcome, (RelevanceReview, ReviewerError)):
            raise TypeError("The relevance reviewer returned an unexpected result type")
        if not isinstance(risk_outcome, (RiskReview, ReviewerError)):
            raise TypeError("The risk reviewer returned an unexpected result type")

        errors = [
            outcome
            for reviewer in self._reviewer_order
            if isinstance((outcome := outcomes[reviewer]), ReviewerError)
        ]
        return ReviewWorkflowResult(
            evidence_review=(
                evidence_outcome if isinstance(evidence_outcome, EvidenceReview) else None
            ),
            relevance_review=(
                relevance_outcome if isinstance(relevance_outcome, RelevanceReview) else None
            ),
            risk_review=risk_outcome if isinstance(risk_outcome, RiskReview) else None,
            errors=errors,
        )

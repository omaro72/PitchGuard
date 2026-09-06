import asyncio

import pytest
from pydantic import ValidationError

from app.providers.errors import ProviderConnectionError, ProviderModelNotFoundError
from app.reviewers.errors import ReviewerContractError
from app.schemas import (
    EvidenceReview,
    RelevanceReview,
    ReviewerError,
    ReviewerName,
    ReviewRequest,
    RiskReview,
)
from app.workflow import ReviewWorkflow, ReviewWorkflowPolicy, ReviewWorkflowResult
from tests.workflow.conftest import FakeReviewer


def make_error(
    reviewer: ReviewerName,
    *,
    code: str = "test_reviewer_error",
    retryable: bool = False,
) -> ReviewerError:
    return ReviewerError(
        reviewer=reviewer,
        code=code,
        message="The fictional reviewer could not complete.",
        retryable=retryable,
    )


def test_policy_accepts_defaults_and_boundaries() -> None:
    assert ReviewWorkflowPolicy() == ReviewWorkflowPolicy(
        max_attempts=2,
        retry_delay_seconds=0.25,
        attempt_timeout_seconds=130,
    )
    assert (
        ReviewWorkflowPolicy(
            max_attempts=1,
            retry_delay_seconds=0,
            attempt_timeout_seconds=1,
        ).max_attempts
        == 1
    )
    assert (
        ReviewWorkflowPolicy(
            max_attempts=3,
            retry_delay_seconds=5,
            attempt_timeout_seconds=600,
        ).max_attempts
        == 3
    )


@pytest.mark.parametrize(
    "values",
    [
        {"max_attempts": 0},
        {"max_attempts": 4},
        {"retry_delay_seconds": -0.01},
        {"retry_delay_seconds": 5.01},
        {"attempt_timeout_seconds": 0},
        {"attempt_timeout_seconds": 601},
    ],
)
def test_policy_rejects_values_outside_bounds(values: dict[str, int | float]) -> None:
    with pytest.raises(ValidationError):
        ReviewWorkflowPolicy(**values)


def test_policy_is_immutable() -> None:
    policy = ReviewWorkflowPolicy()

    with pytest.raises(ValidationError):
        policy.max_attempts = 3


def test_complete_result_reports_derived_state(
    evidence_review: EvidenceReview,
    relevance_review: RelevanceReview,
    risk_review: RiskReview,
) -> None:
    result = ReviewWorkflowResult(
        evidence_review=evidence_review,
        relevance_review=relevance_review,
        risk_review=risk_review,
    )

    assert result.is_complete is True
    assert result.has_errors is False
    assert result.errors == []
    assert "decision" not in type(result).model_fields


def test_partial_and_all_failed_results_are_valid(
    evidence_review: EvidenceReview,
    relevance_review: RelevanceReview,
) -> None:
    partial = ReviewWorkflowResult(
        evidence_review=evidence_review,
        relevance_review=relevance_review,
        risk_review=None,
        errors=[make_error(ReviewerName.RISK)],
    )
    failed = ReviewWorkflowResult(
        errors=[
            make_error(ReviewerName.EVIDENCE),
            make_error(ReviewerName.RELEVANCE),
            make_error(ReviewerName.RISK),
        ]
    )

    assert partial.is_complete is False
    assert partial.has_errors is True
    assert failed.is_complete is False
    assert failed.has_errors is True


def test_result_rejects_success_and_error_for_same_reviewer(
    evidence_review: EvidenceReview,
    relevance_review: RelevanceReview,
    risk_review: RiskReview,
) -> None:
    with pytest.raises(ValidationError, match="EVIDENCE"):
        ReviewWorkflowResult(
            evidence_review=evidence_review,
            relevance_review=relevance_review,
            risk_review=risk_review,
            errors=[make_error(ReviewerName.EVIDENCE)],
        )


def test_result_rejects_duplicate_errors() -> None:
    with pytest.raises(ValidationError, match="duplicate"):
        ReviewWorkflowResult(
            errors=[
                make_error(ReviewerName.EVIDENCE),
                make_error(ReviewerName.EVIDENCE, code="another_error"),
                make_error(ReviewerName.RELEVANCE),
            ]
        )


def test_result_rejects_missing_reviewer_outcome(
    evidence_review: EvidenceReview,
    relevance_review: RelevanceReview,
) -> None:
    with pytest.raises(ValidationError, match="RISK"):
        ReviewWorkflowResult(
            evidence_review=evidence_review,
            relevance_review=relevance_review,
        )


def test_result_cannot_accept_claimed_completion(
    evidence_review: EvidenceReview,
    relevance_review: RelevanceReview,
) -> None:
    with pytest.raises(ValidationError):
        ReviewWorkflowResult.model_validate(
            {
                "evidence_review": evidence_review,
                "relevance_review": relevance_review,
                "errors": [make_error(ReviewerName.RISK)],
                "is_complete": True,
            }
        )


def test_complete_success_is_concurrent_and_identity_safe(
    review_request: ReviewRequest,
    evidence_review: EvidenceReview,
    relevance_review: RelevanceReview,
    risk_review: RiskReview,
) -> None:
    async def scenario() -> None:
        evidence_gate = asyncio.Event()
        relevance_gate = asyncio.Event()
        risk_gate = asyncio.Event()
        evidence = FakeReviewer([evidence_review], finish_gate=evidence_gate)
        relevance = FakeReviewer([relevance_review], finish_gate=relevance_gate)
        risk = FakeReviewer([risk_review], finish_gate=risk_gate)
        workflow = ReviewWorkflow(evidence, relevance, risk)
        original_request = review_request.model_dump()

        workflow_task = asyncio.create_task(workflow.run(review_request))
        await asyncio.wait_for(
            asyncio.gather(
                evidence.started.wait(),
                relevance.started.wait(),
                risk.started.wait(),
            ),
            timeout=1,
        )

        risk_gate.set()
        await asyncio.wait_for(risk.finished.wait(), timeout=1)
        relevance_gate.set()
        await asyncio.wait_for(relevance.finished.wait(), timeout=1)
        evidence_gate.set()
        result = await workflow_task

        assert result.evidence_review is evidence_review
        assert result.relevance_review is relevance_review
        assert result.risk_review is risk_review
        assert result.is_complete is True
        assert result.has_errors is False
        assert result.errors == []
        assert evidence.call_count == relevance.call_count == risk.call_count == 1
        assert evidence.requests == relevance.requests == risk.requests == [review_request]
        assert evidence.requests[0] is review_request
        assert relevance.requests[0] is review_request
        assert risk.requests[0] is review_request
        assert review_request.model_dump() == original_request

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("failed_reviewer", "missing_field"),
    [
        (ReviewerName.EVIDENCE, "evidence_review"),
        (ReviewerName.RELEVANCE, "relevance_review"),
        (ReviewerName.RISK, "risk_review"),
    ],
)
def test_one_expected_failure_preserves_other_results(
    failed_reviewer: ReviewerName,
    missing_field: str,
    review_request: ReviewRequest,
    evidence_review: EvidenceReview,
    relevance_review: RelevanceReview,
    risk_review: RiskReview,
) -> None:
    async def scenario() -> None:
        evidence_outcome: EvidenceReview | Exception = evidence_review
        relevance_outcome: RelevanceReview | Exception = relevance_review
        risk_outcome: RiskReview | Exception = risk_review
        failure = ProviderModelNotFoundError("fictional-model")
        if failed_reviewer is ReviewerName.EVIDENCE:
            evidence_outcome = failure
        elif failed_reviewer is ReviewerName.RELEVANCE:
            relevance_outcome = failure
        else:
            risk_outcome = failure
        evidence = FakeReviewer([evidence_outcome])
        relevance = FakeReviewer([relevance_outcome])
        risk = FakeReviewer([risk_outcome])

        result = await ReviewWorkflow(
            evidence,
            relevance,
            risk,
            ReviewWorkflowPolicy(max_attempts=1),
        ).run(review_request)

        assert getattr(result, missing_field) is None
        assert len(result.errors) == 1
        assert result.errors[0].reviewer is failed_reviewer
        assert result.is_complete is False
        assert result.has_errors is True
        for reviewer, field_name in (
            (ReviewerName.EVIDENCE, "evidence_review"),
            (ReviewerName.RELEVANCE, "relevance_review"),
            (ReviewerName.RISK, "risk_review"),
        ):
            if reviewer is not failed_reviewer:
                assert getattr(result, field_name) is not None

    asyncio.run(scenario())


def test_all_expected_failures_are_ordered_without_duplicates(
    review_request: ReviewRequest,
) -> None:
    async def scenario() -> None:
        evidence_gate = asyncio.Event()
        relevance_gate = asyncio.Event()
        risk_gate = asyncio.Event()
        evidence = FakeReviewer[EvidenceReview](
            [ProviderModelNotFoundError("fictional-model")],
            finish_gate=evidence_gate,
        )
        relevance = FakeReviewer[RelevanceReview](
            [ProviderModelNotFoundError("fictional-model")],
            finish_gate=relevance_gate,
        )
        risk = FakeReviewer[RiskReview](
            [ProviderModelNotFoundError("fictional-model")],
            finish_gate=risk_gate,
        )
        task = asyncio.create_task(
            ReviewWorkflow(
                evidence,
                relevance,
                risk,
                ReviewWorkflowPolicy(max_attempts=1),
            ).run(review_request)
        )
        await asyncio.wait_for(
            asyncio.gather(
                evidence.started.wait(),
                relevance.started.wait(),
                risk.started.wait(),
            ),
            timeout=1,
        )
        risk_gate.set()
        await asyncio.wait_for(risk.finished.wait(), timeout=1)
        relevance_gate.set()
        await asyncio.wait_for(relevance.finished.wait(), timeout=1)
        evidence_gate.set()
        result = await task

        assert result.evidence_review is None
        assert result.relevance_review is None
        assert result.risk_review is None
        assert [error.reviewer for error in result.errors] == [
            ReviewerName.EVIDENCE,
            ReviewerName.RELEVANCE,
            ReviewerName.RISK,
        ]
        assert len({error.reviewer for error in result.errors}) == 3
        assert result.is_complete is False

    asyncio.run(scenario())


def test_retryable_failure_succeeds_without_rerunning_other_reviewers(
    review_request: ReviewRequest,
    evidence_review: EvidenceReview,
    relevance_review: RelevanceReview,
    risk_review: RiskReview,
) -> None:
    async def scenario() -> None:
        evidence = FakeReviewer([ProviderConnectionError(), evidence_review])
        relevance = FakeReviewer([relevance_review])
        risk = FakeReviewer([risk_review])

        result = await ReviewWorkflow(
            evidence,
            relevance,
            risk,
            ReviewWorkflowPolicy(max_attempts=2, retry_delay_seconds=0),
        ).run(review_request)

        assert result.is_complete is True
        assert result.errors == []
        assert evidence.call_count == 2
        assert relevance.call_count == risk.call_count == 1

    asyncio.run(scenario())


def test_retryable_failure_stops_at_max_attempts(
    review_request: ReviewRequest,
    relevance_review: RelevanceReview,
    risk_review: RiskReview,
) -> None:
    async def scenario() -> None:
        evidence = FakeReviewer[EvidenceReview]([ProviderConnectionError()])

        result = await ReviewWorkflow(
            evidence,
            FakeReviewer([relevance_review]),
            FakeReviewer([risk_review]),
            ReviewWorkflowPolicy(max_attempts=3, retry_delay_seconds=0),
        ).run(review_request)

        assert evidence.call_count == 3
        assert result.evidence_review is None
        assert result.relevance_review is relevance_review
        assert result.risk_review is risk_review
        assert len(result.errors) == 1
        assert result.errors[0].reviewer is ReviewerName.EVIDENCE
        assert result.errors[0].retryable is True

    asyncio.run(scenario())


def test_non_retryable_failure_is_not_retried(
    review_request: ReviewRequest,
    relevance_review: RelevanceReview,
    risk_review: RiskReview,
) -> None:
    async def scenario() -> None:
        evidence = FakeReviewer[EvidenceReview]([ProviderModelNotFoundError("fictional-model")])

        result = await ReviewWorkflow(
            evidence,
            FakeReviewer([relevance_review]),
            FakeReviewer([risk_review]),
            ReviewWorkflowPolicy(max_attempts=3, retry_delay_seconds=0),
        ).run(review_request)

        assert evidence.call_count == 1
        assert len(result.errors) == 1
        assert result.errors[0].code == "provider_model_not_found_error"
        assert result.errors[0].retryable is False

    asyncio.run(scenario())


def test_reviewer_contract_error_uses_its_retryability(
    review_request: ReviewRequest,
    evidence_review: EvidenceReview,
    relevance_review: RelevanceReview,
    risk_review: RiskReview,
) -> None:
    async def scenario() -> None:
        contract_error = ReviewerContractError(
            reviewer=ReviewerName.EVIDENCE,
            code="evidence_reference_error",
            message="The evidence reviewer returned an unknown fictional evidence ID.",
            retryable=True,
        )
        evidence = FakeReviewer([contract_error, evidence_review])

        result = await ReviewWorkflow(
            evidence,
            FakeReviewer([relevance_review]),
            FakeReviewer([risk_review]),
            ReviewWorkflowPolicy(max_attempts=2, retry_delay_seconds=0),
        ).run(review_request)

        assert evidence.call_count == 2
        assert result.is_complete is True
        assert result.errors == []

    asyncio.run(scenario())


def test_hanging_attempts_time_out_and_preserve_other_results(
    review_request: ReviewRequest,
    relevance_review: RelevanceReview,
    risk_review: RiskReview,
) -> None:
    async def scenario() -> None:
        evidence = FakeReviewer[EvidenceReview](
            [AssertionError("unreachable")], finish_gate=asyncio.Event()
        )

        result = await ReviewWorkflow(
            evidence,
            FakeReviewer([relevance_review]),
            FakeReviewer([risk_review]),
            ReviewWorkflowPolicy(
                max_attempts=2,
                retry_delay_seconds=0,
                attempt_timeout_seconds=1,
            ),
        ).run(review_request)

        assert evidence.call_count == 2
        assert evidence.cancelled_count == 2
        assert result.evidence_review is None
        assert result.relevance_review is relevance_review
        assert result.risk_review is risk_review
        assert len(result.errors) == 1
        assert result.errors[0] == ReviewerError(
            reviewer=ReviewerName.EVIDENCE,
            code="workflow_attempt_timeout",
            message="The evidence reviewer exceeded the workflow attempt timeout.",
            retryable=True,
        )
        assert review_request.pitch not in result.errors[0].message

    asyncio.run(scenario())


def test_unexpected_exception_is_reraised_and_other_tasks_are_cleaned_up(
    review_request: ReviewRequest,
    evidence_review: EvidenceReview,
    relevance_review: RelevanceReview,
    risk_review: RiskReview,
) -> None:
    async def scenario() -> None:
        evidence_gate = asyncio.Event()
        relevance_gate = asyncio.Event()
        risk_gate = asyncio.Event()
        evidence = FakeReviewer(
            [AttributeError("fictional programming defect")],
            finish_gate=evidence_gate,
        )
        relevance = FakeReviewer([relevance_review], finish_gate=relevance_gate)
        risk = FakeReviewer([risk_review], finish_gate=risk_gate)
        task = asyncio.create_task(ReviewWorkflow(evidence, relevance, risk).run(review_request))
        await asyncio.wait_for(
            asyncio.gather(
                evidence.started.wait(),
                relevance.started.wait(),
                risk.started.wait(),
            ),
            timeout=1,
        )

        evidence_gate.set()
        with pytest.raises(AttributeError, match="fictional programming defect"):
            await task

        assert evidence.call_count == 1
        assert relevance.cancelled_count == 1
        assert risk.cancelled_count == 1
        assert no_pending_workflow_tasks()

    asyncio.run(scenario())


def test_workflow_cancellation_propagates_and_cleans_up_reviewers(
    review_request: ReviewRequest,
    evidence_review: EvidenceReview,
    relevance_review: RelevanceReview,
    risk_review: RiskReview,
) -> None:
    async def scenario() -> None:
        reviewers = (
            FakeReviewer([evidence_review], finish_gate=asyncio.Event()),
            FakeReviewer([relevance_review], finish_gate=asyncio.Event()),
            FakeReviewer([risk_review], finish_gate=asyncio.Event()),
        )
        task = asyncio.create_task(ReviewWorkflow(*reviewers).run(review_request))
        await asyncio.wait_for(
            asyncio.gather(*(reviewer.started.wait() for reviewer in reviewers)),
            timeout=1,
        )

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert all(reviewer.call_count == 1 for reviewer in reviewers)
        assert all(reviewer.cancelled_count == 1 for reviewer in reviewers)
        assert no_pending_workflow_tasks()

    asyncio.run(scenario())


def no_pending_workflow_tasks() -> bool:
    current_task = asyncio.current_task()
    return not any(
        task is not current_task
        and not task.done()
        and task.get_name().startswith("pitchguard-reviewer-")
        for task in asyncio.all_tasks()
    )

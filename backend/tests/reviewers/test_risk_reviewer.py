import asyncio
import json

import pytest

from app.prompts import load_prompt
from app.providers import GenerationOptions, ProviderTimeoutError
from app.reviewers import PRRiskReviewer, ReviewerContractError
from app.schemas import (
    ReviewerName,
    ReviewRequest,
    RiskCategory,
    RiskFinding,
    RiskReview,
    RiskSeverity,
)

from .conftest import RecordingProvider


def risk_finding(
    *,
    category: RiskCategory = RiskCategory.MISLEADING_CERTAINTY,
    pitch_excerpt: str | None = "Our customers save 22% of administrative time.",
    explanation: str = "The statement may sound more certain than the supplied context.",
) -> RiskFinding:
    return RiskFinding(
        category=category,
        severity=RiskSeverity.MEDIUM,
        pitch_excerpt=pitch_excerpt,
        explanation=explanation,
        recommendation="Qualify the statement using the supplied context.",
    )


def risk_review(*findings: RiskFinding) -> RiskReview:
    return RiskReview(
        findings=list(findings) if findings else [risk_finding()],
        summary="One communication risk was identified.",
    )


def run_review(provider: RecordingProvider, request: ReviewRequest) -> RiskReview:
    return asyncio.run(PRRiskReviewer(provider).review(request))


def without_confidential_evidence(request: ReviewRequest) -> ReviewRequest:
    data = request.model_dump(mode="json")
    evidence = data["evidence"]
    assert isinstance(evidence, list)
    for item in evidence:
        item["confidential"] = False
    return ReviewRequest.model_validate(data)


def test_calls_provider_once_with_correct_contract_and_returns_result_unchanged(
    review_request: ReviewRequest,
) -> None:
    result = risk_review()
    provider = RecordingProvider(result)

    returned = run_review(provider, review_request)

    assert returned is result
    assert len(provider.calls) == 1
    call = provider.calls[0]
    assert call.system_prompt == load_prompt("risk-reviewer-v1")
    assert call.response_model is RiskReview
    assert call.options == GenerationOptions(temperature=0.0, max_output_tokens=3_072)
    payload = json.loads(call.user_prompt.partition("\n")[2])
    assert set(payload) == {"campaign", "evidence", "pitch"}


def test_exact_pitch_excerpt_is_accepted(review_request: ReviewRequest) -> None:
    result = risk_review(risk_finding(pitch_excerpt="Would you like the fictional report?"))

    assert run_review(RecordingProvider(result), review_request) is result


def test_pitch_excerpt_across_normalized_whitespace_is_accepted(
    review_request: ReviewRequest,
) -> None:
    data = review_request.model_dump(mode="json")
    data["pitch"] = (
        "Hello Alex, Would you\n like  the fictional report? This remains a fictional example."
    )
    request = ReviewRequest.model_validate(data)
    result = risk_review(risk_finding(pitch_excerpt="Would you like the fictional report?"))

    assert run_review(RecordingProvider(result), request) is result


@pytest.mark.parametrize(
    "pitch_excerpt",
    [
        "This is guaranteed to change everything.",
        "Customers achieve substantial savings.",
    ],
)
def test_invented_or_paraphrased_pitch_excerpt_is_rejected(
    review_request: ReviewRequest,
    pitch_excerpt: str,
) -> None:
    result = risk_review(risk_finding(pitch_excerpt=pitch_excerpt))

    with pytest.raises(ReviewerContractError) as captured:
        run_review(RecordingProvider(result), review_request)

    assert captured.value.code == "invalid_risk_excerpt"


def test_finding_without_optional_excerpt_is_accepted(
    review_request: ReviewRequest,
) -> None:
    result = risk_review(
        risk_finding(
            category=RiskCategory.UNCLEAR_CALL_TO_ACTION,
            pitch_excerpt=None,
        )
    )

    assert run_review(RecordingProvider(result), review_request) is result


def test_duplicate_risk_findings_are_rejected(review_request: ReviewRequest) -> None:
    first = risk_finding()
    duplicate = risk_finding(
        pitch_excerpt="Our customers  save 22%\nof administrative time.",
        explanation="A repeated risk with different explanatory wording.",
    )
    result = risk_review(first, duplicate)

    with pytest.raises(ReviewerContractError) as captured:
        run_review(RecordingProvider(result), review_request)

    assert captured.value.code == "duplicate_risk_finding"


def test_confidentiality_finding_is_accepted_with_confidential_evidence(
    review_request: ReviewRequest,
) -> None:
    result = risk_review(
        risk_finding(
            category=RiskCategory.CONFIDENTIALITY,
            pitch_excerpt="The confidential launch date is 15 October 2026.",
        )
    )

    assert run_review(RecordingProvider(result), review_request) is result


def test_confidentiality_finding_is_rejected_without_confidential_evidence(
    review_request: ReviewRequest,
) -> None:
    request = without_confidential_evidence(review_request)
    result = risk_review(
        risk_finding(
            category=RiskCategory.CONFIDENTIALITY,
            pitch_excerpt="The confidential launch date is 15 October 2026.",
        )
    )

    with pytest.raises(ReviewerContractError) as captured:
        run_review(RecordingProvider(result), request)

    assert captured.value.reviewer is ReviewerName.RISK
    assert captured.value.code == "unsupported_confidentiality_finding"


def test_provider_exception_propagates_without_losing_type(
    review_request: ReviewRequest,
) -> None:
    error = ProviderTimeoutError()
    provider = RecordingProvider(error=error)

    with pytest.raises(ProviderTimeoutError) as captured:
        run_review(provider, review_request)

    assert captured.value is error
    assert len(provider.calls) == 1


def test_contract_error_does_not_expose_complete_submitted_content(
    review_request: ReviewRequest,
) -> None:
    result = risk_review(risk_finding(pitch_excerpt="Invented risky statement."))

    with pytest.raises(ReviewerContractError) as captured:
        run_review(RecordingProvider(result), review_request)

    error_text = str(captured.value)
    assert review_request.pitch not in error_text
    assert all(item.content not in error_text for item in review_request.evidence)

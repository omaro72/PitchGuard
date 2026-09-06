import asyncio
import json

import pytest

from app.prompts import load_prompt
from app.providers import GenerationOptions, ProviderTimeoutError
from app.reviewers import ClaimEvidenceReviewer, ReviewerContractError
from app.schemas import (
    ClaimFinding,
    ClaimImportance,
    ClaimStatus,
    ClaimType,
    EvidenceReview,
    ReviewerName,
    ReviewRequest,
)

from .conftest import RecordingProvider


def claim_finding(
    *,
    claim_text: str = "Our customers save 22% of administrative time.",
    claim_type: ClaimType = ClaimType.STATISTIC,
    status: ClaimStatus = ClaimStatus.SUPPORTED,
    evidence_ids: list[str] | None = None,
    explanation: str = "Evidence E1 supports the percentage and scope.",
) -> ClaimFinding:
    return ClaimFinding(
        claim_text=claim_text,
        claim_type=claim_type,
        importance=ClaimImportance.HIGH,
        status=status,
        explanation=explanation,
        evidence_ids=["E1"] if evidence_ids is None else evidence_ids,
    )


def evidence_review(*claims: ClaimFinding) -> EvidenceReview:
    return EvidenceReview(
        claims=list(claims) if claims else [claim_finding()],
        summary="The supplied claim was reviewed against the supplied evidence.",
    )


def run_review(
    provider: RecordingProvider,
    request: ReviewRequest,
) -> EvidenceReview:
    return asyncio.run(ClaimEvidenceReviewer(provider).review(request))


def without_evidence(request: ReviewRequest) -> ReviewRequest:
    data = request.model_dump(mode="json")
    data["evidence"] = []
    return ReviewRequest.model_validate(data)


def test_calls_provider_once_with_correct_contract_and_returns_result_unchanged(
    review_request: ReviewRequest,
) -> None:
    result = evidence_review()
    provider = RecordingProvider(result)

    returned = run_review(provider, review_request)

    assert returned is result
    assert len(provider.calls) == 1
    call = provider.calls[0]
    assert call.system_prompt == load_prompt("evidence-reviewer-v1")
    assert call.response_model is EvidenceReview
    assert call.options == GenerationOptions(temperature=0.0, max_output_tokens=4_096)
    payload = json.loads(call.user_prompt.partition("\n")[2])
    assert set(payload) == {"campaign", "evidence", "pitch"}


def test_existing_evidence_reference_is_accepted(review_request: ReviewRequest) -> None:
    result = evidence_review(claim_finding(evidence_ids=["E1"]))

    assert run_review(RecordingProvider(result), review_request) is result


def test_nonexistent_evidence_reference_is_rejected(review_request: ReviewRequest) -> None:
    result = evidence_review(claim_finding(status=ClaimStatus.UNSUPPORTED, evidence_ids=["E9"]))

    with pytest.raises(ReviewerContractError) as captured:
        run_review(RecordingProvider(result), review_request)

    assert captured.value.reviewer is ReviewerName.EVIDENCE
    assert captured.value.code == "invalid_evidence_reference"


def test_evidence_reference_is_rejected_when_request_has_no_evidence(
    review_request: ReviewRequest,
) -> None:
    request = without_evidence(review_request)
    result = evidence_review(claim_finding(status=ClaimStatus.UNSUPPORTED, evidence_ids=["E1"]))

    with pytest.raises(ReviewerContractError, match="not supplied"):
        run_review(RecordingProvider(result), request)


def test_exact_claim_excerpt_is_accepted(review_request: ReviewRequest) -> None:
    result = evidence_review(
        claim_finding(claim_text="Our customers save 22% of administrative time.")
    )

    assert run_review(RecordingProvider(result), review_request) is result


def test_claim_excerpt_across_normalized_whitespace_is_accepted(
    review_request: ReviewRequest,
) -> None:
    data = review_request.model_dump(mode="json")
    data["pitch"] = (
        "Hello Alex, Our customers\n save 22%   of administrative time. "
        "Would you like the fictional report?"
    )
    request = ReviewRequest.model_validate(data)
    result = evidence_review(
        claim_finding(claim_text="Our customers save 22% of administrative time.")
    )

    assert run_review(RecordingProvider(result), request) is result


@pytest.mark.parametrize(
    "claim_text",
    [
        "Our customers save 40% of administrative time.",
        "Customers reduce administrative work substantially.",
    ],
)
def test_invented_or_paraphrased_claim_excerpt_is_rejected(
    review_request: ReviewRequest,
    claim_text: str,
) -> None:
    result = evidence_review(
        claim_finding(
            claim_text=claim_text,
            status=ClaimStatus.UNSUPPORTED,
            evidence_ids=[],
        )
    )

    with pytest.raises(ReviewerContractError) as captured:
        run_review(RecordingProvider(result), review_request)

    assert captured.value.code == "invalid_claim_excerpt"


def test_duplicate_claim_findings_are_rejected(review_request: ReviewRequest) -> None:
    first = claim_finding()
    duplicate = claim_finding(
        claim_text="Our customers  save 22%\nof administrative time.",
        explanation="A repeated finding with different explanatory wording.",
    )
    result = evidence_review(first, duplicate)

    with pytest.raises(ReviewerContractError) as captured:
        run_review(RecordingProvider(result), review_request)

    assert captured.value.code == "duplicate_claim_finding"


@pytest.mark.parametrize("status", [ClaimStatus.SUPPORTED, ClaimStatus.CONTRADICTED])
def test_evidence_backed_status_with_real_reference_is_accepted(
    review_request: ReviewRequest,
    status: ClaimStatus,
) -> None:
    result = evidence_review(claim_finding(status=status, evidence_ids=["E1"]))

    assert run_review(RecordingProvider(result), review_request) is result


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
    result = evidence_review(claim_finding(status=ClaimStatus.UNSUPPORTED, evidence_ids=["E9"]))

    with pytest.raises(ReviewerContractError) as captured:
        run_review(RecordingProvider(result), review_request)

    error_text = str(captured.value)
    assert review_request.pitch not in error_text
    assert all(item.content not in error_text for item in review_request.evidence)

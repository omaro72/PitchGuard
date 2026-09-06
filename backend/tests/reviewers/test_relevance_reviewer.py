import asyncio
import json

import pytest

from app.prompts import load_prompt
from app.providers import GenerationOptions, ProviderTimeoutError
from app.reviewers import JournalistRelevanceReviewer, ReviewerContractError
from app.schemas import RelevanceReview, ReviewerName, ReviewRequest

from .conftest import RecordingProvider


def relevance_review(
    *,
    relevance_score: int = 80,
    personalization_score: int = 75,
    matched_topics: list[str] | None = None,
    mismatches: list[str] | None = None,
    missing_context: list[str] | None = None,
) -> RelevanceReview:
    return RelevanceReview(
        relevance_score=relevance_score,
        personalization_score=personalization_score,
        summary="The campaign fits the supplied workplace technology coverage.",
        matched_topics=["Workplace technology"] if matched_topics is None else matched_topics,
        mismatches=[] if mismatches is None else mismatches,
        missing_context=[] if missing_context is None else missing_context,
    )


def run_review(
    provider: RecordingProvider,
    request: ReviewRequest,
) -> RelevanceReview:
    return asyncio.run(JournalistRelevanceReviewer(provider).review(request))


def without_recent_coverage(request: ReviewRequest) -> ReviewRequest:
    data = request.model_dump(mode="json")
    journalist = data["journalist"]
    assert isinstance(journalist, dict)
    journalist["recent_coverage"] = []
    return ReviewRequest.model_validate(data)


def test_calls_provider_once_with_correct_contract_and_returns_result_unchanged(
    review_request: ReviewRequest,
) -> None:
    result = relevance_review()
    provider = RecordingProvider(result)

    returned = run_review(provider, review_request)

    assert returned is result
    assert len(provider.calls) == 1
    call = provider.calls[0]
    assert call.system_prompt == load_prompt("relevance-reviewer-v1")
    assert call.response_model is RelevanceReview
    assert call.options == GenerationOptions(temperature=0.0, max_output_tokens=2_048)
    payload = json.loads(call.user_prompt.partition("\n")[2])
    assert set(payload) == {"campaign", "journalist", "pitch"}


def test_empty_recent_coverage_is_accepted(review_request: ReviewRequest) -> None:
    request = without_recent_coverage(review_request)
    result = relevance_review(missing_context=["No recent coverage was supplied."])

    assert run_review(RecordingProvider(result), request) is result


def test_valid_score_boundaries_are_accepted(review_request: ReviewRequest) -> None:
    result = relevance_review(relevance_score=0, personalization_score=100)

    assert run_review(RecordingProvider(result), review_request) is result


@pytest.mark.parametrize(
    ("field_name", "values"),
    [
        ("matched_topics", ["Workplace technology", "Workplace\n technology"]),
        ("mismatches", ["No privacy angle", "No  privacy angle"]),
        ("missing_context", ["No audience detail", "No\n audience detail"]),
    ],
)
def test_duplicate_normalized_entries_are_rejected(
    review_request: ReviewRequest,
    field_name: str,
    values: list[str],
) -> None:
    arguments = {field_name: values}
    result = relevance_review(**arguments)

    with pytest.raises(ReviewerContractError) as captured:
        run_review(RecordingProvider(result), review_request)

    assert captured.value.reviewer is ReviewerName.RELEVANCE
    assert captured.value.code == "duplicate_relevance_statement"


@pytest.mark.parametrize("field_name", ["matched_topics", "mismatches", "missing_context"])
def test_empty_list_entries_are_rejected(
    review_request: ReviewRequest,
    field_name: str,
) -> None:
    result = relevance_review(**{field_name: ["   "]})

    with pytest.raises(ReviewerContractError) as captured:
        run_review(RecordingProvider(result), review_request)

    assert captured.value.code == "empty_relevance_statement"


def test_same_normalized_match_and_mismatch_is_rejected(
    review_request: ReviewRequest,
) -> None:
    result = relevance_review(
        matched_topics=["Workplace technology"],
        mismatches=["Workplace\n technology"],
    )

    with pytest.raises(ReviewerContractError) as captured:
        run_review(RecordingProvider(result), review_request)

    assert captured.value.code == "conflicting_relevance_statement"


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
    result = relevance_review(matched_topics=["Duplicate", "Duplicate"])

    with pytest.raises(ReviewerContractError) as captured:
        run_review(RecordingProvider(result), review_request)

    error_text = str(captured.value)
    assert review_request.pitch not in error_text
    assert review_request.campaign.announcement not in error_text
    assert review_request.journalist.beat not in error_text

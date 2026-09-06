from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas import (
    AnalysisStatus,
    CampaignBrief,
    ClaimFinding,
    ClaimImportance,
    ClaimStatus,
    ClaimType,
    CoverageItem,
    EvidenceItem,
    EvidenceReview,
    JournalistProfile,
    RelevanceReview,
    ReviewDecision,
    ReviewerError,
    ReviewerName,
    ReviewRequest,
    ReviewResponse,
    RiskCategory,
    RiskFinding,
    RiskReview,
    RiskSeverity,
)


def campaign_data() -> dict[str, object]:
    return {
        "company_name": "Acme Research",
        "announcement": "Acme Research is publishing a fictional workplace study.",
        "target_audience": "Technology and workplace journalists",
    }


def evidence_data(item_id: str = "E1") -> dict[str, object]:
    return {
        "id": item_id,
        "source": "Fictional internal study",
        "content": "The fictional study included 120 consenting participants.",
    }


def coverage_data(item_id: str = "C1") -> dict[str, object]:
    return {
        "id": item_id,
        "title": "How teams evaluate workplace software",
        "summary": "A fictional article about workplace technology evaluation.",
    }


def journalist_data() -> dict[str, object]:
    return {
        "name": "Alex Morgan",
        "publication": "Example News",
        "beat": "Workplace technology",
        "recent_coverage": [coverage_data()],
    }


def review_request_data() -> dict[str, object]:
    return {
        "campaign": campaign_data(),
        "evidence": [evidence_data()],
        "journalist": journalist_data(),
        "pitch": "Would you be interested in reviewing this fictional workplace study?",
    }


def claim_finding(
    status: ClaimStatus = ClaimStatus.SUPPORTED,
    evidence_ids: list[str] | None = None,
) -> ClaimFinding:
    return ClaimFinding(
        claim_text="The fictional study included 120 participants.",
        claim_type=ClaimType.STATISTIC,
        importance=ClaimImportance.HIGH,
        status=status,
        explanation="The participant count matches the supplied evidence.",
        evidence_ids=["E1"] if evidence_ids is None else evidence_ids,
    )


def evidence_review() -> EvidenceReview:
    return EvidenceReview(
        claims=[claim_finding()],
        summary="The measurable claim is supported by the supplied evidence.",
    )


def relevance_review(
    relevance_score: int = 80,
    personalization_score: int = 70,
) -> RelevanceReview:
    return RelevanceReview(
        relevance_score=relevance_score,
        personalization_score=personalization_score,
        summary="The subject is relevant to the journalist's supplied beat.",
    )


def risk_review() -> RiskReview:
    return RiskReview(
        findings=[
            RiskFinding(
                category=RiskCategory.UNCLEAR_CALL_TO_ACTION,
                severity=RiskSeverity.LOW,
                pitch_excerpt="Would you be interested?",
                explanation="The requested next step could be more specific.",
                recommendation="Ask whether the journalist wants the fictional study.",
            )
        ],
        summary="No serious risk was found in the supplied text.",
    )


def reviewer_error() -> ReviewerError:
    return ReviewerError(
        reviewer=ReviewerName.EVIDENCE,
        code="MODEL_TIMEOUT",
        message="The local reviewer did not respond in time.",
        retryable=True,
    )


def complete_response_data() -> dict[str, object]:
    return {
        "analysis_status": AnalysisStatus.COMPLETE,
        "decision": ReviewDecision.PASS,
        "decision_reasons": ["All required reviewer results are complete."],
        "evidence_review": evidence_review(),
        "relevance_review": relevance_review(),
        "risk_review": risk_review(),
    }


def test_complete_review_request_is_valid() -> None:
    request = ReviewRequest.model_validate(review_request_data())

    assert request.campaign.company_name == "Acme Research"
    assert request.evidence[0].id == "E1"
    assert request.journalist.recent_coverage[0].id == "C1"


def test_review_request_accepts_empty_evidence() -> None:
    data = review_request_data()
    data["evidence"] = []

    request = ReviewRequest.model_validate(data)

    assert request.evidence == []


def test_journalist_accepts_empty_recent_coverage() -> None:
    profile = JournalistProfile(
        name="Alex Morgan",
        publication="Example News",
        beat="Workplace technology",
    )

    assert profile.recent_coverage == []


def test_coverage_accepts_optional_url_and_publication_date() -> None:
    coverage = CoverageItem(
        **coverage_data(),
        publication_date=date(2026, 9, 1),
        url="https://example.com/articles/workplace-technology",
    )

    assert coverage.publication_date == date(2026, 9, 1)
    assert str(coverage.url) == "https://example.com/articles/workplace-technology"


def test_strings_are_trimmed() -> None:
    data = review_request_data()
    campaign = campaign_data()
    campaign["company_name"] = "  Acme Research  "
    data["campaign"] = campaign
    data["pitch"] = "  Would you be interested in this fictional workplace study?  "

    request = ReviewRequest.model_validate(data)

    assert request.campaign.company_name == "Acme Research"
    assert request.pitch == "Would you be interested in this fictional workplace study?"


def test_missing_required_field_is_rejected() -> None:
    data = campaign_data()
    del data["company_name"]

    with pytest.raises(ValidationError):
        CampaignBrief.model_validate(data)


@pytest.mark.parametrize("field_name", ["company_name", "announcement", "target_audience"])
def test_blank_campaign_fields_are_rejected(field_name: str) -> None:
    data = campaign_data()
    data[field_name] = "   "

    with pytest.raises(ValidationError):
        CampaignBrief.model_validate(data)


def test_blank_pitch_is_rejected() -> None:
    data = review_request_data()
    data["pitch"] = "   "

    with pytest.raises(ValidationError):
        ReviewRequest.model_validate(data)


def test_short_announcement_is_rejected() -> None:
    data = campaign_data()
    data["announcement"] = "Too short"

    with pytest.raises(ValidationError):
        CampaignBrief.model_validate(data)


def test_short_pitch_is_rejected() -> None:
    data = review_request_data()
    data["pitch"] = "Too short"

    with pytest.raises(ValidationError):
        ReviewRequest.model_validate(data)


def test_text_over_maximum_length_is_rejected() -> None:
    data = campaign_data()
    data["company_name"] = "x" * 121

    with pytest.raises(ValidationError):
        CampaignBrief.model_validate(data)


@pytest.mark.parametrize("item_id", ["E0", "e1", "evidence-1", "E-1"])
def test_invalid_evidence_id_is_rejected(item_id: str) -> None:
    with pytest.raises(ValidationError):
        EvidenceItem.model_validate(evidence_data(item_id))


@pytest.mark.parametrize("item_id", ["C0", "c1", "coverage-1", "C-1"])
def test_invalid_coverage_id_is_rejected(item_id: str) -> None:
    with pytest.raises(ValidationError):
        CoverageItem.model_validate(coverage_data(item_id))


def test_duplicate_evidence_ids_are_rejected() -> None:
    data = review_request_data()
    data["evidence"] = [evidence_data("E1"), evidence_data("E1")]

    with pytest.raises(ValidationError):
        ReviewRequest.model_validate(data)


def test_duplicate_coverage_ids_are_rejected() -> None:
    data = review_request_data()
    journalist = journalist_data()
    journalist["recent_coverage"] = [coverage_data("C1"), coverage_data("C1")]
    data["journalist"] = journalist

    with pytest.raises(ValidationError):
        ReviewRequest.model_validate(data)


def test_more_than_ten_evidence_items_are_rejected() -> None:
    data = review_request_data()
    data["evidence"] = [evidence_data(f"E{index}") for index in range(1, 12)]

    with pytest.raises(ValidationError):
        ReviewRequest.model_validate(data)


def test_more_than_ten_coverage_items_are_rejected() -> None:
    data = journalist_data()
    data["recent_coverage"] = [coverage_data(f"C{index}") for index in range(1, 12)]

    with pytest.raises(ValidationError):
        JournalistProfile.model_validate(data)


def test_unexpected_fields_are_rejected() -> None:
    data = review_request_data()
    data["unexpected"] = "value"

    with pytest.raises(ValidationError):
        ReviewRequest.model_validate(data)


def test_relevance_score_boundaries_are_accepted() -> None:
    review = relevance_review(relevance_score=0, personalization_score=100)

    assert review.relevance_score == 0
    assert review.personalization_score == 100


@pytest.mark.parametrize(
    ("field_name", "score"),
    [
        ("relevance_score", -1),
        ("relevance_score", 101),
        ("personalization_score", -1),
        ("personalization_score", 101),
    ],
)
def test_scores_outside_boundaries_are_rejected(field_name: str, score: int) -> None:
    data = {
        "relevance_score": 50,
        "personalization_score": 50,
        "summary": "The supplied context supports a neutral relevance assessment.",
    }
    data[field_name] = score

    with pytest.raises(ValidationError):
        RelevanceReview.model_validate(data)


def test_invalid_enum_value_is_rejected() -> None:
    data = {
        "claim_text": "A fictional claim",
        "claim_type": "OPINION",
        "importance": ClaimImportance.LOW,
        "status": ClaimStatus.UNCLEAR,
        "explanation": "The claim type is not part of the accepted contract.",
    }

    with pytest.raises(ValidationError):
        ClaimFinding.model_validate(data)


@pytest.mark.parametrize("status", [ClaimStatus.SUPPORTED, ClaimStatus.CONTRADICTED])
def test_evidence_backed_status_without_evidence_is_rejected(status: ClaimStatus) -> None:
    with pytest.raises(ValidationError):
        claim_finding(status=status, evidence_ids=[])


def test_duplicate_evidence_references_are_rejected() -> None:
    with pytest.raises(ValidationError):
        claim_finding(evidence_ids=["E1", "E1"])


def test_invalid_evidence_reference_is_rejected() -> None:
    with pytest.raises(ValidationError):
        claim_finding(evidence_ids=["e1"])


def test_valid_reviewer_outputs_are_accepted() -> None:
    evidence_result = evidence_review()
    relevance_result = relevance_review()
    risk_result = risk_review()

    assert len(evidence_result.claims) == 1
    assert relevance_result.relevance_score == 80
    assert len(risk_result.findings) == 1


def test_blank_risk_excerpt_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RiskFinding(
            category=RiskCategory.OTHER,
            severity=RiskSeverity.LOW,
            pitch_excerpt="   ",
            explanation="The supplied excerpt is blank.",
            recommendation="Omit the excerpt when it is unavailable.",
        )


def test_enum_values_are_serialized_as_strings() -> None:
    serialized = claim_finding().model_dump(mode="json")

    assert serialized["status"] == "SUPPORTED"
    assert serialized["claim_type"] == "STATISTIC"


def test_valid_complete_response_is_accepted() -> None:
    response = ReviewResponse.model_validate(complete_response_data())

    assert response.analysis_status == AnalysisStatus.COMPLETE
    assert response.decision == ReviewDecision.PASS


def test_complete_response_without_decision_is_rejected() -> None:
    data = complete_response_data()
    data["decision"] = None

    with pytest.raises(ValidationError):
        ReviewResponse.model_validate(data)


@pytest.mark.parametrize("field_name", ["evidence_review", "relevance_review", "risk_review"])
def test_complete_response_without_reviewer_result_is_rejected(field_name: str) -> None:
    data = complete_response_data()
    data[field_name] = None

    with pytest.raises(ValidationError):
        ReviewResponse.model_validate(data)


def test_complete_response_with_errors_is_rejected() -> None:
    data = complete_response_data()
    data["errors"] = [reviewer_error()]

    with pytest.raises(ValidationError):
        ReviewResponse.model_validate(data)


def test_valid_error_response_is_accepted() -> None:
    response = ReviewResponse(
        analysis_status=AnalysisStatus.ERROR,
        errors=[reviewer_error()],
    )

    assert response.decision is None
    assert len(response.errors) == 1


def test_error_response_with_decision_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ReviewResponse(
            analysis_status=AnalysisStatus.ERROR,
            decision=ReviewDecision.BLOCK,
            errors=[reviewer_error()],
        )


def test_error_response_without_errors_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ReviewResponse(analysis_status=AnalysisStatus.ERROR)


def test_error_response_with_decision_reasons_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ReviewResponse(
            analysis_status=AnalysisStatus.ERROR,
            decision_reasons=["A completed decision was not produced."],
            errors=[reviewer_error()],
        )


def test_error_response_preserves_partial_results() -> None:
    response = ReviewResponse(
        analysis_status=AnalysisStatus.ERROR,
        evidence_review=evidence_review(),
        errors=[reviewer_error()],
    )

    assert response.evidence_review is not None
    assert response.relevance_review is None
    assert response.risk_review is None

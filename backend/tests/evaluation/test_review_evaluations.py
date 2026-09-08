import asyncio
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Literal, Self

import pytest
from pydantic import ConfigDict, Field, ValidationError, model_validator

from app.decision import DecisionEngine, DecisionReasonCode, DecisionResult
from app.reviewers import ClaimEvidenceReviewer, JournalistRelevanceReviewer, PRRiskReviewer
from app.schemas import (
    ClaimStatus,
    EvidenceReview,
    PitchGuardSchema,
    RelevanceReview,
    ReviewDecision,
    ReviewRequest,
    RiskCategory,
    RiskReview,
)
from app.workflow import ReviewWorkflow
from tests.reviewers.conftest import RecordingProvider

FIXTURE_DIRECTORY = Path(__file__).parents[1] / "fixtures" / "evaluation"
CASE_NAMES = ("pass_case", "revise_case", "block_case")


class ScoreRange(PitchGuardSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)

    minimum: int = Field(ge=0, le=100)
    maximum: int = Field(ge=0, le=100)

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.minimum > self.maximum:
            raise ValueError("minimum score cannot exceed maximum score")
        return self


class EvaluationExpectations(PitchGuardSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)

    required_claim_statuses: list[ClaimStatus]
    required_risk_categories: list[RiskCategory]
    relevance_score_range: ScoreRange
    personalization_score_range: ScoreRange


class MockedReviewerOutputs(PitchGuardSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_review: EvidenceReview
    relevance_review: RelevanceReview
    risk_review: RiskReview


class EvaluationCase(PitchGuardSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str = Field(min_length=1, max_length=100)
    fictional: Literal[True]
    request: ReviewRequest
    mocked_outputs: MockedReviewerOutputs
    expected_decision: ReviewDecision
    expected_reason_codes: list[DecisionReasonCode] = Field(min_length=1)
    expectations: EvaluationExpectations


def load_evaluation_case(path: Path) -> EvaluationCase:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise AssertionError(f"Could not read evaluation fixture {path.name}") from error
    except JSONDecodeError as error:
        raise AssertionError(f"Evaluation fixture {path.name} contains invalid JSON") from error

    try:
        return EvaluationCase.model_validate(payload)
    except ValidationError as error:
        raise AssertionError(
            f"Evaluation fixture {path.name} does not match the evaluation schema"
        ) from error


def decision_reason_codes(decision: DecisionResult) -> set[DecisionReasonCode]:
    codes = set(decision.reason_codes)
    if decision.pass_reason_code is not None:
        codes.add(decision.pass_reason_code)
    return codes


def assert_score_in_range(score: int, expected_range: ScoreRange) -> None:
    assert expected_range.minimum <= score <= expected_range.maximum


def test_fixture_directory_contains_only_the_declared_cases() -> None:
    fixture_names = {path.stem for path in FIXTURE_DIRECTORY.glob("*.json")}

    assert fixture_names == set(CASE_NAMES)


@pytest.mark.parametrize("case_name", CASE_NAMES)
def test_fictional_review_evaluation(case_name: str) -> None:
    case = load_evaluation_case(FIXTURE_DIRECTORY / f"{case_name}.json")
    outputs = case.mocked_outputs
    evidence_provider = RecordingProvider(result=outputs.evidence_review)
    relevance_provider = RecordingProvider(result=outputs.relevance_review)
    risk_provider = RecordingProvider(result=outputs.risk_review)
    workflow = ReviewWorkflow(
        ClaimEvidenceReviewer(evidence_provider),
        JournalistRelevanceReviewer(relevance_provider),
        PRRiskReviewer(risk_provider),
    )

    workflow_result = asyncio.run(workflow.run(case.request))
    decision = DecisionEngine().evaluate(workflow_result)

    assert case.case_id == case_name
    assert isinstance(case.request, ReviewRequest)
    assert isinstance(outputs.evidence_review, EvidenceReview)
    assert isinstance(outputs.relevance_review, RelevanceReview)
    assert isinstance(outputs.risk_review, RiskReview)
    assert workflow_result.is_complete is True
    assert workflow_result.errors == []
    assert decision.decision is case.expected_decision
    assert decision_reason_codes(decision) == set(case.expected_reason_codes)

    actual_claim_statuses = {claim.status for claim in outputs.evidence_review.claims}
    actual_risk_categories = {finding.category for finding in outputs.risk_review.findings}
    assert set(case.expectations.required_claim_statuses) <= actual_claim_statuses
    assert set(case.expectations.required_risk_categories) <= actual_risk_categories
    assert_score_in_range(
        outputs.relevance_review.relevance_score,
        case.expectations.relevance_score_range,
    )
    assert_score_in_range(
        outputs.relevance_review.personalization_score,
        case.expectations.personalization_score_range,
    )
    assert [
        len(provider.calls) for provider in (evidence_provider, relevance_provider, risk_provider)
    ] == [
        1,
        1,
        1,
    ]


def test_fixture_loader_reports_invalid_json_clearly(tmp_path: Path) -> None:
    fixture_path = tmp_path / "broken_case.json"
    fixture_path.write_text("{", encoding="utf-8")

    with pytest.raises(AssertionError, match="broken_case.json contains invalid JSON"):
        load_evaluation_case(fixture_path)


def test_fixture_loader_reports_schema_errors_clearly(tmp_path: Path) -> None:
    fixture_path = tmp_path / "broken_case.json"
    fixture_path.write_text('{"case_id": "broken_case"}', encoding="utf-8")

    with pytest.raises(AssertionError, match="broken_case.json does not match"):
        load_evaluation_case(fixture_path)

from collections.abc import Callable

import pytest

from app.schemas import (
    ClaimFinding,
    ClaimImportance,
    ClaimStatus,
    ClaimType,
    EvidenceReview,
    RelevanceReview,
    RiskCategory,
    RiskFinding,
    RiskReview,
    RiskSeverity,
)
from app.workflow import ReviewWorkflowResult

type ClaimFindingFactory = Callable[..., ClaimFinding]
type EvidenceReviewFactory = Callable[..., EvidenceReview]
type RelevanceReviewFactory = Callable[..., RelevanceReview]
type RiskFindingFactory = Callable[..., RiskFinding]
type RiskReviewFactory = Callable[..., RiskReview]
type WorkflowResultFactory = Callable[..., ReviewWorkflowResult]


@pytest.fixture
def claim_finding_factory() -> ClaimFindingFactory:
    def make_claim_finding(
        status: ClaimStatus = ClaimStatus.SUPPORTED,
        importance: ClaimImportance = ClaimImportance.HIGH,
        claim_text: str = "The fictional study included 120 participants.",
        explanation: str = "The fictional claim was compared with the supplied evidence.",
    ) -> ClaimFinding:
        evidence_ids = ["E1"] if status in {ClaimStatus.SUPPORTED, ClaimStatus.CONTRADICTED} else []
        return ClaimFinding(
            claim_text=claim_text,
            claim_type=ClaimType.STATISTIC,
            importance=importance,
            status=status,
            explanation=explanation,
            evidence_ids=evidence_ids,
        )

    return make_claim_finding


@pytest.fixture
def evidence_review_factory(
    claim_finding_factory: ClaimFindingFactory,
) -> EvidenceReviewFactory:
    def make_evidence_review(
        claims: list[ClaimFinding] | None = None,
        missing_context: list[str] | None = None,
        summary: str = "The fictional claims were checked against supplied evidence.",
    ) -> EvidenceReview:
        return EvidenceReview(
            claims=[claim_finding_factory()] if claims is None else claims,
            summary=summary,
            missing_context=[] if missing_context is None else missing_context,
        )

    return make_evidence_review


@pytest.fixture
def relevance_review_factory() -> RelevanceReviewFactory:
    def make_relevance_review(
        relevance_score: int = 70,
        personalization_score: int = 60,
        missing_context: list[str] | None = None,
        summary: str = "The fictional pitch matches the supplied journalist profile.",
    ) -> RelevanceReview:
        return RelevanceReview(
            relevance_score=relevance_score,
            personalization_score=personalization_score,
            summary=summary,
            matched_topics=["fictional workplace research"],
            mismatches=[],
            missing_context=[] if missing_context is None else missing_context,
        )

    return make_relevance_review


@pytest.fixture
def risk_finding_factory() -> RiskFindingFactory:
    def make_risk_finding(
        severity: RiskSeverity = RiskSeverity.LOW,
        category: RiskCategory = RiskCategory.OTHER,
        explanation: str = "A fictional language issue was identified.",
    ) -> RiskFinding:
        return RiskFinding(
            category=category,
            severity=severity,
            pitch_excerpt=None,
            explanation=explanation,
            recommendation="Review the fictional wording before use.",
        )

    return make_risk_finding


@pytest.fixture
def risk_review_factory() -> RiskReviewFactory:
    def make_risk_review(
        findings: list[RiskFinding] | None = None,
        missing_context: list[str] | None = None,
        summary: str = "No material risk was found in the fictional pitch.",
    ) -> RiskReview:
        return RiskReview(
            findings=[] if findings is None else findings,
            summary=summary,
            missing_context=[] if missing_context is None else missing_context,
        )

    return make_risk_review


@pytest.fixture
def complete_workflow_result_factory(
    evidence_review_factory: EvidenceReviewFactory,
    relevance_review_factory: RelevanceReviewFactory,
    risk_review_factory: RiskReviewFactory,
) -> WorkflowResultFactory:
    def make_workflow_result(
        evidence_review: EvidenceReview | None = None,
        relevance_review: RelevanceReview | None = None,
        risk_review: RiskReview | None = None,
    ) -> ReviewWorkflowResult:
        return ReviewWorkflowResult(
            evidence_review=(
                evidence_review if evidence_review is not None else evidence_review_factory()
            ),
            relevance_review=(
                relevance_review if relevance_review is not None else relevance_review_factory()
            ),
            risk_review=risk_review if risk_review is not None else risk_review_factory(),
        )

    return make_workflow_result

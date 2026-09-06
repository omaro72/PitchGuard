from datetime import date
from enum import StrEnum
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    field_validator,
    model_validator,
)

EvidenceId = Annotated[str, StringConstraints(pattern=r"^E[1-9][0-9]*$")]
CoverageId = Annotated[str, StringConstraints(pattern=r"^C[1-9][0-9]*$")]


def require_unique_ids(values: list[str], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates")


class PitchGuardSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ClaimStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNCLEAR = "UNCLEAR"


class ClaimType(StrEnum):
    STATISTIC = "STATISTIC"
    COMPARISON = "COMPARISON"
    MARKET_LEADERSHIP = "MARKET_LEADERSHIP"
    PERFORMANCE = "PERFORMANCE"
    FACTUAL = "FACTUAL"
    OTHER = "OTHER"


class ClaimImportance(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RiskSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(StrEnum):
    EXCESSIVE_PROMOTION = "EXCESSIVE_PROMOTION"
    UNSUPPORTED_SUPERLATIVE = "UNSUPPORTED_SUPERLATIVE"
    MISLEADING_CERTAINTY = "MISLEADING_CERTAINTY"
    SPAM_LIKE_LANGUAGE = "SPAM_LIKE_LANGUAGE"
    UNCLEAR_CALL_TO_ACTION = "UNCLEAR_CALL_TO_ACTION"
    CONFIDENTIALITY = "CONFIDENTIALITY"
    REPUTATIONAL = "REPUTATIONAL"
    OTHER = "OTHER"


class ReviewDecision(StrEnum):
    PASS = "PASS"
    REVISE = "REVISE"
    BLOCK = "BLOCK"


class AnalysisStatus(StrEnum):
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


class ReviewerName(StrEnum):
    EVIDENCE = "EVIDENCE"
    RELEVANCE = "RELEVANCE"
    RISK = "RISK"


class CampaignBrief(PitchGuardSchema):
    company_name: str = Field(min_length=1, max_length=120)
    announcement: str = Field(min_length=20, max_length=5_000)
    target_audience: str = Field(min_length=1, max_length=1_000)


class EvidenceItem(PitchGuardSchema):
    id: EvidenceId
    source: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=10, max_length=5_000)
    confidential: bool = False


class CoverageItem(PitchGuardSchema):
    id: CoverageId
    title: str = Field(min_length=1, max_length=300)
    summary: str = Field(min_length=10, max_length=3_000)
    publication_date: date | None = None
    url: HttpUrl | None = None


class JournalistProfile(PitchGuardSchema):
    name: str = Field(min_length=1, max_length=120)
    publication: str = Field(min_length=1, max_length=200)
    beat: str = Field(min_length=1, max_length=1_000)
    recent_coverage: list[CoverageItem] = Field(default_factory=list, max_length=10)


class ReviewRequest(PitchGuardSchema):
    campaign: CampaignBrief
    evidence: list[EvidenceItem] = Field(default_factory=list, max_length=10)
    journalist: JournalistProfile
    pitch: str = Field(min_length=20, max_length=5_000)

    @model_validator(mode="after")
    def validate_unique_item_ids(self) -> Self:
        require_unique_ids([item.id for item in self.evidence], "evidence IDs")
        require_unique_ids(
            [item.id for item in self.journalist.recent_coverage],
            "recent coverage IDs",
        )
        return self


class ClaimFinding(PitchGuardSchema):
    claim_text: str = Field(min_length=1, max_length=1_000)
    claim_type: ClaimType
    importance: ClaimImportance
    status: ClaimStatus
    explanation: str = Field(min_length=1, max_length=2_000)
    evidence_ids: list[EvidenceId] = Field(default_factory=list, max_length=10)

    @field_validator("evidence_ids")
    @classmethod
    def validate_unique_evidence_ids(cls, evidence_ids: list[str]) -> list[str]:
        require_unique_ids(evidence_ids, "evidence IDs")
        return evidence_ids

    @model_validator(mode="after")
    def validate_evidence_backed_status(self) -> Self:
        evidence_backed_statuses = {ClaimStatus.SUPPORTED, ClaimStatus.CONTRADICTED}
        if self.status in evidence_backed_statuses and not self.evidence_ids:
            raise ValueError(f"{self.status.value} claims require at least one evidence ID")
        return self


class EvidenceReview(PitchGuardSchema):
    claims: list[ClaimFinding] = Field(default_factory=list, max_length=30)
    summary: str = Field(min_length=1, max_length=2_000)
    missing_context: list[str] = Field(default_factory=list, max_length=10)


class RelevanceReview(PitchGuardSchema):
    relevance_score: int = Field(ge=0, le=100)
    personalization_score: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1, max_length=2_000)
    matched_topics: list[str] = Field(default_factory=list, max_length=10)
    mismatches: list[str] = Field(default_factory=list, max_length=10)
    missing_context: list[str] = Field(default_factory=list, max_length=10)


class RiskFinding(PitchGuardSchema):
    category: RiskCategory
    severity: RiskSeverity
    pitch_excerpt: str | None = Field(default=None, min_length=1, max_length=1_000)
    explanation: str = Field(min_length=1, max_length=2_000)
    recommendation: str = Field(min_length=1, max_length=2_000)


class RiskReview(PitchGuardSchema):
    findings: list[RiskFinding] = Field(default_factory=list, max_length=30)
    summary: str = Field(min_length=1, max_length=2_000)
    missing_context: list[str] = Field(default_factory=list, max_length=10)


class ReviewerError(PitchGuardSchema):
    reviewer: ReviewerName
    code: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=1_000)
    retryable: bool = False


class ReviewResponse(PitchGuardSchema):
    analysis_status: AnalysisStatus
    decision: ReviewDecision | None = None
    decision_reasons: list[str] = Field(default_factory=list, max_length=20)
    evidence_review: EvidenceReview | None = None
    relevance_review: RelevanceReview | None = None
    risk_review: RiskReview | None = None
    errors: list[ReviewerError] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def validate_analysis_status(self) -> Self:
        if self.analysis_status is AnalysisStatus.COMPLETE:
            required_fields = {
                "decision": self.decision,
                "evidence_review": self.evidence_review,
                "relevance_review": self.relevance_review,
                "risk_review": self.risk_review,
            }
            missing_fields = [name for name, value in required_fields.items() if value is None]
            if missing_fields:
                missing = ", ".join(missing_fields)
                raise ValueError(f"COMPLETE analysis requires: {missing}")
            if self.errors:
                raise ValueError("COMPLETE analysis cannot contain reviewer errors")
            return self

        if self.decision is not None:
            raise ValueError("ERROR analysis cannot contain a decision")
        if not self.errors:
            raise ValueError("ERROR analysis requires at least one reviewer error")
        if self.decision_reasons:
            raise ValueError("ERROR analysis cannot contain decision reasons")
        return self

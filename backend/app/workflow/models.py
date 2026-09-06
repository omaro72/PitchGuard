from typing import Self

from pydantic import ConfigDict, Field, model_validator

from app.schemas import (
    EvidenceReview,
    PitchGuardSchema,
    RelevanceReview,
    ReviewerError,
    ReviewerName,
    RiskReview,
)


class ReviewWorkflowResult(PitchGuardSchema):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    evidence_review: EvidenceReview | None = None
    relevance_review: RelevanceReview | None = None
    risk_review: RiskReview | None = None
    errors: list[ReviewerError] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def validate_reviewer_outcomes(self) -> Self:
        errors_by_reviewer: dict[ReviewerName, ReviewerError] = {}
        for error in self.errors:
            if error.reviewer in errors_by_reviewer:
                raise ValueError(f"duplicate final error for {error.reviewer.value}")
            errors_by_reviewer[error.reviewer] = error

        reviews = {
            ReviewerName.EVIDENCE: self.evidence_review,
            ReviewerName.RELEVANCE: self.relevance_review,
            ReviewerName.RISK: self.risk_review,
        }
        for reviewer, review in reviews.items():
            has_error = reviewer in errors_by_reviewer
            if review is not None and has_error:
                raise ValueError(f"{reviewer.value} cannot have both a result and an error")
            if review is None and not has_error:
                raise ValueError(f"{reviewer.value} requires either a result or an error")
        return self

    @property
    def is_complete(self) -> bool:
        return (
            self.evidence_review is not None
            and self.relevance_review is not None
            and self.risk_review is not None
            and not self.errors
        )

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

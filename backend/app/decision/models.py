from enum import StrEnum
from typing import Self

from pydantic import ConfigDict, Field, model_validator

from app.schemas import PitchGuardSchema, ReviewDecision, ReviewerName


class DecisionReasonCode(StrEnum):
    BLOCK_HIGH_IMPORTANCE_CONTRADICTION = "BLOCK_HIGH_IMPORTANCE_CONTRADICTION"
    BLOCK_CRITICAL_RISK = "BLOCK_CRITICAL_RISK"
    BLOCK_HIGH_CONFIDENTIALITY_RISK = "BLOCK_HIGH_CONFIDENTIALITY_RISK"
    BLOCK_LOW_RELEVANCE = "BLOCK_LOW_RELEVANCE"
    REVISE_OTHER_CONTRADICTION = "REVISE_OTHER_CONTRADICTION"
    REVISE_UNSUPPORTED_MATERIAL_CLAIM = "REVISE_UNSUPPORTED_MATERIAL_CLAIM"
    REVISE_UNCLEAR_MATERIAL_CLAIM = "REVISE_UNCLEAR_MATERIAL_CLAIM"
    REVISE_PARTIAL_RELEVANCE = "REVISE_PARTIAL_RELEVANCE"
    REVISE_LOW_PERSONALIZATION = "REVISE_LOW_PERSONALIZATION"
    REVISE_ACTIONABLE_RISK = "REVISE_ACTIONABLE_RISK"
    REVISE_MISSING_CONTEXT = "REVISE_MISSING_CONTEXT"
    PASS_QUALITY_GATE_CLEAR = "PASS_QUALITY_GATE_CLEAR"


_BLOCKING_CODES = frozenset(
    {
        DecisionReasonCode.BLOCK_HIGH_IMPORTANCE_CONTRADICTION,
        DecisionReasonCode.BLOCK_CRITICAL_RISK,
        DecisionReasonCode.BLOCK_HIGH_CONFIDENTIALITY_RISK,
        DecisionReasonCode.BLOCK_LOW_RELEVANCE,
    }
)
_PASS_REASON = "No deterministic blocking or revision condition was triggered."


class DecisionFinding(PitchGuardSchema):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    code: DecisionReasonCode
    target_decision: ReviewDecision
    message: str = Field(min_length=1, max_length=500)
    source: ReviewerName

    @model_validator(mode="after")
    def validate_target_decision(self) -> Self:
        if self.code is DecisionReasonCode.PASS_QUALITY_GATE_CLEAR:
            raise ValueError("PASS_QUALITY_GATE_CLEAR cannot be a decision finding")
        expected_decision = (
            ReviewDecision.BLOCK if self.code in _BLOCKING_CODES else ReviewDecision.REVISE
        )
        if self.target_decision is not expected_decision:
            raise ValueError(f"{self.code.value} must target {expected_decision.value}")
        return self


class DecisionResult(PitchGuardSchema):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    decision: ReviewDecision
    findings: list[DecisionFinding] = Field(default_factory=list, max_length=11)
    pass_reason_code: DecisionReasonCode | None = None

    @model_validator(mode="after")
    def validate_decision(self) -> Self:
        reason_codes = [finding.code for finding in self.findings]
        if len(reason_codes) != len(set(reason_codes)):
            raise ValueError("decision findings cannot contain duplicate reason codes")

        blocking_findings = [
            finding for finding in self.findings if finding.target_decision is ReviewDecision.BLOCK
        ]
        revision_findings = [
            finding for finding in self.findings if finding.target_decision is ReviewDecision.REVISE
        ]
        if self.decision is ReviewDecision.BLOCK:
            if not blocking_findings:
                raise ValueError("BLOCK requires at least one blocking finding")
            if self.pass_reason_code is not None:
                raise ValueError("BLOCK cannot contain a pass reason")
            return self

        if self.decision is ReviewDecision.REVISE:
            if blocking_findings or not revision_findings:
                raise ValueError(
                    "REVISE requires revision findings and cannot contain blocking findings"
                )
            if self.pass_reason_code is not None:
                raise ValueError("REVISE cannot contain a pass reason")
            return self

        if self.findings:
            raise ValueError("PASS cannot contain blocking or revision findings")
        if self.pass_reason_code is not DecisionReasonCode.PASS_QUALITY_GATE_CLEAR:
            raise ValueError("PASS requires PASS_QUALITY_GATE_CLEAR")
        return self

    @property
    def reason_codes(self) -> list[DecisionReasonCode]:
        return [finding.code for finding in self.findings]

    @property
    def reasons(self) -> list[str]:
        return [finding.message for finding in self.findings]

    @property
    def pass_reason(self) -> str | None:
        if self.pass_reason_code is DecisionReasonCode.PASS_QUALITY_GATE_CLEAR:
            return _PASS_REASON
        return None

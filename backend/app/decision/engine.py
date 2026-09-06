from app.decision.errors import IncompleteWorkflowError
from app.decision.models import DecisionFinding, DecisionReasonCode, DecisionResult
from app.decision.policy import DecisionPolicy
from app.schemas import (
    ClaimImportance,
    ClaimStatus,
    EvidenceReview,
    RelevanceReview,
    ReviewDecision,
    ReviewerName,
    RiskCategory,
    RiskReview,
    RiskSeverity,
)
from app.workflow import ReviewWorkflowResult


class DecisionEngine:
    def __init__(self, policy: DecisionPolicy | None = None) -> None:
        self._policy = policy or DecisionPolicy()

    def evaluate(self, workflow_result: ReviewWorkflowResult) -> DecisionResult:
        evidence_review, relevance_review, risk_review = self._require_complete(workflow_result)
        findings = [
            finding
            for finding in (
                self._high_importance_contradiction(evidence_review),
                self._critical_risk(risk_review),
                self._high_confidentiality_risk(risk_review),
                self._low_relevance(relevance_review),
                self._other_contradiction(evidence_review),
                self._unsupported_material_claim(evidence_review),
                self._unclear_material_claim(evidence_review),
                self._partial_relevance(relevance_review),
                self._low_personalization(relevance_review),
                self._actionable_risk(risk_review),
                self._missing_context(
                    evidence_review,
                    relevance_review,
                    risk_review,
                ),
            )
            if finding is not None
        ]

        if any(finding.target_decision is ReviewDecision.BLOCK for finding in findings):
            decision = ReviewDecision.BLOCK
        elif findings:
            decision = ReviewDecision.REVISE
        else:
            decision = ReviewDecision.PASS

        return DecisionResult(
            decision=decision,
            findings=findings,
            pass_reason_code=(
                DecisionReasonCode.PASS_QUALITY_GATE_CLEAR
                if decision is ReviewDecision.PASS
                else None
            ),
        )

    @staticmethod
    def _require_complete(
        workflow_result: ReviewWorkflowResult,
    ) -> tuple[EvidenceReview, RelevanceReview, RiskReview]:
        evidence_review = workflow_result.evidence_review
        relevance_review = workflow_result.relevance_review
        risk_review = workflow_result.risk_review
        if (
            not workflow_result.is_complete
            or workflow_result.errors
            or evidence_review is None
            or relevance_review is None
            or risk_review is None
        ):
            raise IncompleteWorkflowError()
        return evidence_review, relevance_review, risk_review

    @staticmethod
    def _high_importance_contradiction(
        evidence_review: EvidenceReview,
    ) -> DecisionFinding | None:
        if not any(
            claim.status is ClaimStatus.CONTRADICTED and claim.importance is ClaimImportance.HIGH
            for claim in evidence_review.claims
        ):
            return None
        return DecisionFinding(
            code=DecisionReasonCode.BLOCK_HIGH_IMPORTANCE_CONTRADICTION,
            target_decision=ReviewDecision.BLOCK,
            message="At least one high-importance claim contradicts the supplied evidence.",
            source=ReviewerName.EVIDENCE,
        )

    @staticmethod
    def _critical_risk(risk_review: RiskReview) -> DecisionFinding | None:
        if not any(finding.severity is RiskSeverity.CRITICAL for finding in risk_review.findings):
            return None
        return DecisionFinding(
            code=DecisionReasonCode.BLOCK_CRITICAL_RISK,
            target_decision=ReviewDecision.BLOCK,
            message="At least one critical PR or reputational risk was detected.",
            source=ReviewerName.RISK,
        )

    @staticmethod
    def _high_confidentiality_risk(
        risk_review: RiskReview,
    ) -> DecisionFinding | None:
        if not any(
            finding.category is RiskCategory.CONFIDENTIALITY
            and finding.severity in {RiskSeverity.HIGH, RiskSeverity.CRITICAL}
            for finding in risk_review.findings
        ):
            return None
        return DecisionFinding(
            code=DecisionReasonCode.BLOCK_HIGH_CONFIDENTIALITY_RISK,
            target_decision=ReviewDecision.BLOCK,
            message="The pitch may expose information explicitly identified as confidential.",
            source=ReviewerName.RISK,
        )

    def _low_relevance(
        self,
        relevance_review: RelevanceReview,
    ) -> DecisionFinding | None:
        score = relevance_review.relevance_score
        if score >= self._policy.block_relevance_below:
            return None
        return DecisionFinding(
            code=DecisionReasonCode.BLOCK_LOW_RELEVANCE,
            target_decision=ReviewDecision.BLOCK,
            message=f"Journalist relevance is below the minimum threshold: {score}/100.",
            source=ReviewerName.RELEVANCE,
        )

    @staticmethod
    def _other_contradiction(
        evidence_review: EvidenceReview,
    ) -> DecisionFinding | None:
        if not any(
            claim.status is ClaimStatus.CONTRADICTED
            and claim.importance in {ClaimImportance.LOW, ClaimImportance.MEDIUM}
            for claim in evidence_review.claims
        ):
            return None
        return DecisionFinding(
            code=DecisionReasonCode.REVISE_OTHER_CONTRADICTION,
            target_decision=ReviewDecision.REVISE,
            message=(
                "At least one claim conflicts with the supplied evidence and should be corrected."
            ),
            source=ReviewerName.EVIDENCE,
        )

    @staticmethod
    def _unsupported_material_claim(
        evidence_review: EvidenceReview,
    ) -> DecisionFinding | None:
        if not any(
            claim.status is ClaimStatus.UNSUPPORTED
            and claim.importance in {ClaimImportance.MEDIUM, ClaimImportance.HIGH}
            for claim in evidence_review.claims
        ):
            return None
        return DecisionFinding(
            code=DecisionReasonCode.REVISE_UNSUPPORTED_MATERIAL_CLAIM,
            target_decision=ReviewDecision.REVISE,
            message="At least one material claim is not supported by the supplied evidence.",
            source=ReviewerName.EVIDENCE,
        )

    @staticmethod
    def _unclear_material_claim(
        evidence_review: EvidenceReview,
    ) -> DecisionFinding | None:
        if not any(
            claim.status is ClaimStatus.UNCLEAR
            and claim.importance in {ClaimImportance.MEDIUM, ClaimImportance.HIGH}
            for claim in evidence_review.claims
        ):
            return None
        return DecisionFinding(
            code=DecisionReasonCode.REVISE_UNCLEAR_MATERIAL_CLAIM,
            target_decision=ReviewDecision.REVISE,
            message=(
                "At least one material claim cannot be assessed clearly from the supplied "
                "information."
            ),
            source=ReviewerName.EVIDENCE,
        )

    def _partial_relevance(
        self,
        relevance_review: RelevanceReview,
    ) -> DecisionFinding | None:
        score = relevance_review.relevance_score
        if not (self._policy.block_relevance_below <= score < self._policy.pass_relevance_at_least):
            return None
        return DecisionFinding(
            code=DecisionReasonCode.REVISE_PARTIAL_RELEVANCE,
            target_decision=ReviewDecision.REVISE,
            message=f"Journalist relevance needs improvement: {score}/100.",
            source=ReviewerName.RELEVANCE,
        )

    def _low_personalization(
        self,
        relevance_review: RelevanceReview,
    ) -> DecisionFinding | None:
        score = relevance_review.personalization_score
        if score >= self._policy.minimum_personalization:
            return None
        return DecisionFinding(
            code=DecisionReasonCode.REVISE_LOW_PERSONALIZATION,
            target_decision=ReviewDecision.REVISE,
            message=f"Pitch personalization is below the required threshold: {score}/100.",
            source=ReviewerName.RELEVANCE,
        )

    @staticmethod
    def _actionable_risk(risk_review: RiskReview) -> DecisionFinding | None:
        if not any(
            finding.severity in {RiskSeverity.MEDIUM, RiskSeverity.HIGH}
            and not (
                finding.category is RiskCategory.CONFIDENTIALITY
                and finding.severity is RiskSeverity.HIGH
            )
            for finding in risk_review.findings
        ):
            return None
        return DecisionFinding(
            code=DecisionReasonCode.REVISE_ACTIONABLE_RISK,
            target_decision=ReviewDecision.REVISE,
            message="At least one PR risk should be corrected before the pitch is used.",
            source=ReviewerName.RISK,
        )

    @staticmethod
    def _missing_context(
        evidence_review: EvidenceReview,
        relevance_review: RelevanceReview,
        risk_review: RiskReview,
    ) -> DecisionFinding | None:
        for reviewer, missing_context in (
            (ReviewerName.EVIDENCE, evidence_review.missing_context),
            (ReviewerName.RELEVANCE, relevance_review.missing_context),
            (ReviewerName.RISK, risk_review.missing_context),
        ):
            if missing_context:
                return DecisionFinding(
                    code=DecisionReasonCode.REVISE_MISSING_CONTEXT,
                    target_decision=ReviewDecision.REVISE,
                    message="Additional context is required for a reliable pitch review.",
                    source=reviewer,
                )
        return None

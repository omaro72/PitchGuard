from app.reviewers.errors import ReviewerContractError
from app.schemas import (
    ClaimStatus,
    ClaimType,
    EvidenceReview,
    RelevanceReview,
    ReviewerName,
    ReviewRequest,
    RiskCategory,
    RiskReview,
)


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def _require_excerpt(
    *,
    excerpt: str,
    source: str,
    reviewer: ReviewerName,
    code: str,
    message: str,
) -> str:
    normalized_excerpt = normalize_text(excerpt)
    if not normalized_excerpt or normalized_excerpt not in normalize_text(source):
        raise ReviewerContractError(
            reviewer=reviewer,
            code=code,
            message=message,
        )
    return normalized_excerpt


def _normalized_statements(
    values: list[str],
    *,
    field_name: str,
) -> set[str]:
    normalized_values: set[str] = set()
    for value in values:
        normalized = normalize_text(value)
        if not normalized:
            raise ReviewerContractError(
                reviewer=ReviewerName.RELEVANCE,
                code="empty_relevance_statement",
                message=f"Relevance reviewer returned an empty {field_name} entry.",
            )
        if normalized in normalized_values:
            raise ReviewerContractError(
                reviewer=ReviewerName.RELEVANCE,
                code="duplicate_relevance_statement",
                message=f"Relevance reviewer returned duplicate {field_name} entries.",
            )
        normalized_values.add(normalized)
    return normalized_values


def validate_evidence_result(result: EvidenceReview, request: ReviewRequest) -> None:
    supplied_evidence_ids = {item.id for item in request.evidence}
    evidence_backed_statuses = {ClaimStatus.SUPPORTED, ClaimStatus.CONTRADICTED}
    finding_keys: set[tuple[str, ClaimType]] = set()

    for finding in result.claims:
        if any(evidence_id not in supplied_evidence_ids for evidence_id in finding.evidence_ids):
            raise ReviewerContractError(
                reviewer=ReviewerName.EVIDENCE,
                code="invalid_evidence_reference",
                message="Evidence reviewer returned an evidence reference that was not supplied.",
            )
        if finding.status in evidence_backed_statuses and not finding.evidence_ids:
            raise ReviewerContractError(
                reviewer=ReviewerName.EVIDENCE,
                code="missing_evidence_reference",
                message="Evidence reviewer returned an evidence-backed status without evidence.",
            )

        normalized_claim = _require_excerpt(
            excerpt=finding.claim_text,
            source=request.pitch,
            reviewer=ReviewerName.EVIDENCE,
            code="invalid_claim_excerpt",
            message="Evidence reviewer returned a claim excerpt that does not appear in the pitch.",
        )
        finding_key = (normalized_claim, finding.claim_type)
        if finding_key in finding_keys:
            raise ReviewerContractError(
                reviewer=ReviewerName.EVIDENCE,
                code="duplicate_claim_finding",
                message="Evidence reviewer returned duplicate claim findings.",
            )
        finding_keys.add(finding_key)


def validate_relevance_result(result: RelevanceReview) -> None:
    matched_topics = _normalized_statements(
        result.matched_topics,
        field_name="matched_topics",
    )
    mismatches = _normalized_statements(
        result.mismatches,
        field_name="mismatches",
    )
    _normalized_statements(
        result.missing_context,
        field_name="missing_context",
    )

    if matched_topics & mismatches:
        raise ReviewerContractError(
            reviewer=ReviewerName.RELEVANCE,
            code="conflicting_relevance_statement",
            message=(
                "Relevance reviewer returned the same statement as both a match and a mismatch."
            ),
        )


def validate_risk_result(result: RiskReview, request: ReviewRequest) -> None:
    has_confidential_evidence = any(item.confidential for item in request.evidence)
    finding_keys: set[tuple[RiskCategory, str | None]] = set()

    for finding in result.findings:
        normalized_excerpt = None
        if finding.pitch_excerpt is not None:
            normalized_excerpt = _require_excerpt(
                excerpt=finding.pitch_excerpt,
                source=request.pitch,
                reviewer=ReviewerName.RISK,
                code="invalid_risk_excerpt",
                message="Risk reviewer returned an excerpt that does not appear in the pitch.",
            )

        finding_key = (finding.category, normalized_excerpt)
        if finding_key in finding_keys:
            raise ReviewerContractError(
                reviewer=ReviewerName.RISK,
                code="duplicate_risk_finding",
                message="Risk reviewer returned duplicate risk findings.",
            )
        finding_keys.add(finding_key)

        if finding.category is RiskCategory.CONFIDENTIALITY and not has_confidential_evidence:
            raise ReviewerContractError(
                reviewer=ReviewerName.RISK,
                code="unsupported_confidentiality_finding",
                message=(
                    "Risk reviewer returned a confidentiality finding without "
                    "confidential evidence."
                ),
            )

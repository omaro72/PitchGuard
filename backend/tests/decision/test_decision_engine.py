import pytest
from pydantic import ValidationError

from app.decision import (
    DecisionEngine,
    DecisionFinding,
    DecisionPolicy,
    DecisionReasonCode,
    DecisionResult,
    IncompleteWorkflowError,
)
from app.schemas import (
    ClaimImportance,
    ClaimStatus,
    ReviewDecision,
    ReviewerError,
    ReviewerName,
    RiskCategory,
    RiskSeverity,
)
from app.workflow import ReviewWorkflowResult
from tests.decision.conftest import (
    ClaimFindingFactory,
    EvidenceReviewFactory,
    RelevanceReviewFactory,
    RiskFindingFactory,
    RiskReviewFactory,
    WorkflowResultFactory,
)


def test_reason_code_contract_is_exact() -> None:
    assert list(DecisionReasonCode) == [
        DecisionReasonCode.BLOCK_HIGH_IMPORTANCE_CONTRADICTION,
        DecisionReasonCode.BLOCK_CRITICAL_RISK,
        DecisionReasonCode.BLOCK_HIGH_CONFIDENTIALITY_RISK,
        DecisionReasonCode.BLOCK_LOW_RELEVANCE,
        DecisionReasonCode.REVISE_OTHER_CONTRADICTION,
        DecisionReasonCode.REVISE_UNSUPPORTED_MATERIAL_CLAIM,
        DecisionReasonCode.REVISE_UNCLEAR_MATERIAL_CLAIM,
        DecisionReasonCode.REVISE_PARTIAL_RELEVANCE,
        DecisionReasonCode.REVISE_LOW_PERSONALIZATION,
        DecisionReasonCode.REVISE_ACTIONABLE_RISK,
        DecisionReasonCode.REVISE_MISSING_CONTEXT,
        DecisionReasonCode.PASS_QUALITY_GATE_CLEAR,
    ]


def test_default_policy_is_valid_and_immutable() -> None:
    policy = DecisionPolicy()

    assert policy.block_relevance_below == 40
    assert policy.pass_relevance_at_least == 70
    assert policy.minimum_personalization == 60
    with pytest.raises(ValidationError):
        policy.block_relevance_below = 30


@pytest.mark.parametrize(
    "values",
    [
        {"block_relevance_below": -1},
        {"block_relevance_below": 101},
        {"pass_relevance_at_least": -1},
        {"pass_relevance_at_least": 101},
        {"minimum_personalization": -1},
        {"minimum_personalization": 101},
        {"block_relevance_below": 40, "pass_relevance_at_least": 40},
        {"block_relevance_below": 70, "pass_relevance_at_least": 40},
    ],
)
def test_policy_rejects_invalid_thresholds(values: dict[str, int]) -> None:
    with pytest.raises(ValidationError):
        DecisionPolicy(**values)


def test_valid_custom_policy_changes_boundaries(
    complete_workflow_result_factory: WorkflowResultFactory,
    relevance_review_factory: RelevanceReviewFactory,
) -> None:
    engine = DecisionEngine(
        DecisionPolicy(
            block_relevance_below=20,
            pass_relevance_at_least=80,
            minimum_personalization=50,
        )
    )

    assert (
        engine.evaluate(
            complete_workflow_result_factory(relevance_review=relevance_review_factory(19, 50))
        ).decision
        is ReviewDecision.BLOCK
    )
    assert (
        engine.evaluate(
            complete_workflow_result_factory(relevance_review=relevance_review_factory(20, 50))
        ).decision
        is ReviewDecision.REVISE
    )
    assert (
        engine.evaluate(
            complete_workflow_result_factory(relevance_review=relevance_review_factory(79, 50))
        ).decision
        is ReviewDecision.REVISE
    )
    assert (
        engine.evaluate(
            complete_workflow_result_factory(relevance_review=relevance_review_factory(80, 50))
        ).decision
        is ReviewDecision.PASS
    )
    assert (
        engine.evaluate(
            complete_workflow_result_factory(relevance_review=relevance_review_factory(80, 49))
        ).decision
        is ReviewDecision.REVISE
    )


@pytest.mark.parametrize(
    ("missing_reviewer", "missing_field"),
    [
        (ReviewerName.EVIDENCE, "evidence_review"),
        (ReviewerName.RELEVANCE, "relevance_review"),
        (ReviewerName.RISK, "risk_review"),
    ],
)
def test_incomplete_workflow_is_rejected(
    missing_reviewer: ReviewerName,
    missing_field: str,
    evidence_review_factory: EvidenceReviewFactory,
    relevance_review_factory: RelevanceReviewFactory,
    risk_review_factory: RiskReviewFactory,
) -> None:
    values: dict[str, object] = {
        "evidence_review": evidence_review_factory(),
        "relevance_review": relevance_review_factory(),
        "risk_review": risk_review_factory(),
    }
    values[missing_field] = None
    values["errors"] = [
        ReviewerError(
            reviewer=missing_reviewer,
            code="fictional_reviewer_failure",
            message="The fictional reviewer did not complete.",
            retryable=False,
        )
    ]
    workflow_result = ReviewWorkflowResult.model_validate(values)

    assert workflow_result.is_complete is False
    with pytest.raises(IncompleteWorkflowError, match="incomplete"):
        DecisionEngine().evaluate(workflow_result)


def test_incomplete_error_message_does_not_expose_reviewer_content(
    evidence_review_factory: EvidenceReviewFactory,
    relevance_review_factory: RelevanceReviewFactory,
) -> None:
    sensitive_text = "FICTIONAL-SENSITIVE-REVIEW-CONTENT"
    workflow_result = ReviewWorkflowResult(
        evidence_review=evidence_review_factory(summary=sensitive_text),
        relevance_review=relevance_review_factory(),
        errors=[
            ReviewerError(
                reviewer=ReviewerName.RISK,
                code="fictional_failure",
                message="The risk reviewer did not complete.",
            )
        ],
    )

    with pytest.raises(IncompleteWorkflowError) as captured:
        DecisionEngine().evaluate(workflow_result)

    assert sensitive_text not in str(captured.value)


def test_passing_result_uses_inclusive_quality_boundaries(
    complete_workflow_result_factory: WorkflowResultFactory,
    risk_review_factory: RiskReviewFactory,
    risk_finding_factory: RiskFindingFactory,
) -> None:
    result = DecisionEngine().evaluate(
        complete_workflow_result_factory(
            risk_review=risk_review_factory(findings=[risk_finding_factory(RiskSeverity.LOW)])
        )
    )

    assert result.decision is ReviewDecision.PASS
    assert result.findings == []
    assert result.reason_codes == []
    assert result.reasons == []
    assert result.pass_reason_code is DecisionReasonCode.PASS_QUALITY_GATE_CLEAR
    assert result.pass_reason == "No deterministic blocking or revision condition was triggered."


@pytest.mark.parametrize(
    ("score", "expected_decision", "expected_code"),
    [
        (39, ReviewDecision.BLOCK, DecisionReasonCode.BLOCK_LOW_RELEVANCE),
        (40, ReviewDecision.REVISE, DecisionReasonCode.REVISE_PARTIAL_RELEVANCE),
        (69, ReviewDecision.REVISE, DecisionReasonCode.REVISE_PARTIAL_RELEVANCE),
        (70, ReviewDecision.PASS, None),
        (100, ReviewDecision.PASS, None),
    ],
)
def test_relevance_boundaries(
    score: int,
    expected_decision: ReviewDecision,
    expected_code: DecisionReasonCode | None,
    complete_workflow_result_factory: WorkflowResultFactory,
    relevance_review_factory: RelevanceReviewFactory,
) -> None:
    result = DecisionEngine().evaluate(
        complete_workflow_result_factory(relevance_review=relevance_review_factory(score, 60))
    )

    assert result.decision is expected_decision
    if expected_code is None:
        assert not result.findings
    else:
        assert result.reason_codes == [expected_code]


@pytest.mark.parametrize(
    ("score", "expected_decision", "expected_code"),
    [
        (0, ReviewDecision.REVISE, DecisionReasonCode.REVISE_LOW_PERSONALIZATION),
        (59, ReviewDecision.REVISE, DecisionReasonCode.REVISE_LOW_PERSONALIZATION),
        (60, ReviewDecision.PASS, None),
        (100, ReviewDecision.PASS, None),
    ],
)
def test_personalization_boundaries(
    score: int,
    expected_decision: ReviewDecision,
    expected_code: DecisionReasonCode | None,
    complete_workflow_result_factory: WorkflowResultFactory,
    relevance_review_factory: RelevanceReviewFactory,
) -> None:
    result = DecisionEngine().evaluate(
        complete_workflow_result_factory(relevance_review=relevance_review_factory(70, score))
    )

    assert result.decision is expected_decision
    if expected_code is None:
        assert not result.findings
    else:
        assert result.reason_codes == [expected_code]


@pytest.mark.parametrize(
    ("status", "importance", "expected_decision", "expected_code"),
    [
        (
            ClaimStatus.CONTRADICTED,
            ClaimImportance.HIGH,
            ReviewDecision.BLOCK,
            DecisionReasonCode.BLOCK_HIGH_IMPORTANCE_CONTRADICTION,
        ),
        (
            ClaimStatus.CONTRADICTED,
            ClaimImportance.MEDIUM,
            ReviewDecision.REVISE,
            DecisionReasonCode.REVISE_OTHER_CONTRADICTION,
        ),
        (
            ClaimStatus.CONTRADICTED,
            ClaimImportance.LOW,
            ReviewDecision.REVISE,
            DecisionReasonCode.REVISE_OTHER_CONTRADICTION,
        ),
        (
            ClaimStatus.UNSUPPORTED,
            ClaimImportance.HIGH,
            ReviewDecision.REVISE,
            DecisionReasonCode.REVISE_UNSUPPORTED_MATERIAL_CLAIM,
        ),
        (
            ClaimStatus.UNSUPPORTED,
            ClaimImportance.MEDIUM,
            ReviewDecision.REVISE,
            DecisionReasonCode.REVISE_UNSUPPORTED_MATERIAL_CLAIM,
        ),
        (ClaimStatus.UNSUPPORTED, ClaimImportance.LOW, ReviewDecision.PASS, None),
        (
            ClaimStatus.UNCLEAR,
            ClaimImportance.HIGH,
            ReviewDecision.REVISE,
            DecisionReasonCode.REVISE_UNCLEAR_MATERIAL_CLAIM,
        ),
        (
            ClaimStatus.UNCLEAR,
            ClaimImportance.MEDIUM,
            ReviewDecision.REVISE,
            DecisionReasonCode.REVISE_UNCLEAR_MATERIAL_CLAIM,
        ),
        (ClaimStatus.UNCLEAR, ClaimImportance.LOW, ReviewDecision.PASS, None),
        (ClaimStatus.SUPPORTED, ClaimImportance.HIGH, ReviewDecision.PASS, None),
    ],
)
def test_claim_rules(
    status: ClaimStatus,
    importance: ClaimImportance,
    expected_decision: ReviewDecision,
    expected_code: DecisionReasonCode | None,
    claim_finding_factory: ClaimFindingFactory,
    evidence_review_factory: EvidenceReviewFactory,
    complete_workflow_result_factory: WorkflowResultFactory,
) -> None:
    evidence_review = evidence_review_factory(claims=[claim_finding_factory(status, importance)])

    result = DecisionEngine().evaluate(
        complete_workflow_result_factory(evidence_review=evidence_review)
    )

    assert result.decision is expected_decision
    if expected_code is None:
        assert not result.findings
    else:
        assert result.reason_codes == [expected_code]


@pytest.mark.parametrize("category", list(RiskCategory))
def test_critical_risk_blocks_for_every_category(
    category: RiskCategory,
    risk_finding_factory: RiskFindingFactory,
    risk_review_factory: RiskReviewFactory,
    complete_workflow_result_factory: WorkflowResultFactory,
) -> None:
    workflow_result = complete_workflow_result_factory(
        risk_review=risk_review_factory(
            findings=[risk_finding_factory(RiskSeverity.CRITICAL, category)]
        )
    )

    result = DecisionEngine().evaluate(workflow_result)

    assert result.decision is ReviewDecision.BLOCK
    assert DecisionReasonCode.BLOCK_CRITICAL_RISK in result.reason_codes
    if category is RiskCategory.CONFIDENTIALITY:
        assert DecisionReasonCode.BLOCK_HIGH_CONFIDENTIALITY_RISK in result.reason_codes
    else:
        assert DecisionReasonCode.BLOCK_HIGH_CONFIDENTIALITY_RISK not in result.reason_codes


@pytest.mark.parametrize(
    ("severity", "category", "expected_decision", "expected_code"),
    [
        (
            RiskSeverity.HIGH,
            RiskCategory.CONFIDENTIALITY,
            ReviewDecision.BLOCK,
            DecisionReasonCode.BLOCK_HIGH_CONFIDENTIALITY_RISK,
        ),
        (
            RiskSeverity.MEDIUM,
            RiskCategory.CONFIDENTIALITY,
            ReviewDecision.REVISE,
            DecisionReasonCode.REVISE_ACTIONABLE_RISK,
        ),
        (
            RiskSeverity.HIGH,
            RiskCategory.REPUTATIONAL,
            ReviewDecision.REVISE,
            DecisionReasonCode.REVISE_ACTIONABLE_RISK,
        ),
        (
            RiskSeverity.MEDIUM,
            RiskCategory.OTHER,
            ReviewDecision.REVISE,
            DecisionReasonCode.REVISE_ACTIONABLE_RISK,
        ),
        (RiskSeverity.LOW, RiskCategory.OTHER, ReviewDecision.PASS, None),
    ],
)
def test_noncritical_risk_rules(
    severity: RiskSeverity,
    category: RiskCategory,
    expected_decision: ReviewDecision,
    expected_code: DecisionReasonCode | None,
    risk_finding_factory: RiskFindingFactory,
    risk_review_factory: RiskReviewFactory,
    complete_workflow_result_factory: WorkflowResultFactory,
) -> None:
    workflow_result = complete_workflow_result_factory(
        risk_review=risk_review_factory(findings=[risk_finding_factory(severity, category)])
    )

    result = DecisionEngine().evaluate(workflow_result)

    assert result.decision is expected_decision
    if expected_code is None:
        assert not result.findings
    else:
        assert result.reason_codes == [expected_code]


def test_no_risk_findings_create_no_risk_reason(
    complete_workflow_result_factory: WorkflowResultFactory,
) -> None:
    result = DecisionEngine().evaluate(complete_workflow_result_factory())

    risk_codes = {
        DecisionReasonCode.BLOCK_CRITICAL_RISK,
        DecisionReasonCode.BLOCK_HIGH_CONFIDENTIALITY_RISK,
        DecisionReasonCode.REVISE_ACTIONABLE_RISK,
    }
    assert not risk_codes.intersection(result.reason_codes)


@pytest.mark.parametrize(
    "reviewer",
    [ReviewerName.EVIDENCE, ReviewerName.RELEVANCE, ReviewerName.RISK],
)
def test_missing_context_from_each_reviewer_requires_revision(
    reviewer: ReviewerName,
    evidence_review_factory: EvidenceReviewFactory,
    relevance_review_factory: RelevanceReviewFactory,
    risk_review_factory: RiskReviewFactory,
    complete_workflow_result_factory: WorkflowResultFactory,
) -> None:
    evidence_review = evidence_review_factory()
    relevance_review = relevance_review_factory()
    risk_review = risk_review_factory()
    if reviewer is ReviewerName.EVIDENCE:
        evidence_review = evidence_review_factory(missing_context=["Fictional sample detail"])
    elif reviewer is ReviewerName.RELEVANCE:
        relevance_review = relevance_review_factory(missing_context=["Fictional coverage detail"])
    else:
        risk_review = risk_review_factory(missing_context=["Fictional approval detail"])

    result = DecisionEngine().evaluate(
        complete_workflow_result_factory(
            evidence_review=evidence_review,
            relevance_review=relevance_review,
            risk_review=risk_review,
        )
    )

    assert result.decision is ReviewDecision.REVISE
    assert result.reason_codes == [DecisionReasonCode.REVISE_MISSING_CONTEXT]
    assert result.findings[0].source is reviewer


def test_missing_context_is_aggregated_across_reviewers(
    evidence_review_factory: EvidenceReviewFactory,
    relevance_review_factory: RelevanceReviewFactory,
    risk_review_factory: RiskReviewFactory,
    complete_workflow_result_factory: WorkflowResultFactory,
) -> None:
    result = DecisionEngine().evaluate(
        complete_workflow_result_factory(
            evidence_review=evidence_review_factory(missing_context=["Fictional evidence gap"]),
            relevance_review=relevance_review_factory(
                missing_context=["Fictional profile gap", "Fictional coverage gap"]
            ),
            risk_review=risk_review_factory(missing_context=["Fictional risk gap"]),
        )
    )

    assert result.reason_codes.count(DecisionReasonCode.REVISE_MISSING_CONTEXT) == 1
    assert result.findings[-1].source is ReviewerName.EVIDENCE


def test_block_precedence_keeps_all_revision_findings(
    claim_finding_factory: ClaimFindingFactory,
    evidence_review_factory: EvidenceReviewFactory,
    relevance_review_factory: RelevanceReviewFactory,
    risk_finding_factory: RiskFindingFactory,
    risk_review_factory: RiskReviewFactory,
    complete_workflow_result_factory: WorkflowResultFactory,
) -> None:
    workflow_result = complete_workflow_result_factory(
        evidence_review=evidence_review_factory(
            claims=[
                claim_finding_factory(
                    ClaimStatus.UNSUPPORTED,
                    ClaimImportance.HIGH,
                )
            ]
        ),
        relevance_review=relevance_review_factory(39, 59),
        risk_review=risk_review_factory(findings=[risk_finding_factory(RiskSeverity.MEDIUM)]),
    )

    result = DecisionEngine().evaluate(workflow_result)

    assert result.decision is ReviewDecision.BLOCK
    assert result.reason_codes == [
        DecisionReasonCode.BLOCK_LOW_RELEVANCE,
        DecisionReasonCode.REVISE_UNSUPPORTED_MATERIAL_CLAIM,
        DecisionReasonCode.REVISE_LOW_PERSONALIZATION,
        DecisionReasonCode.REVISE_ACTIONABLE_RISK,
    ]


def test_several_revision_rules_return_revise(
    claim_finding_factory: ClaimFindingFactory,
    evidence_review_factory: EvidenceReviewFactory,
    relevance_review_factory: RelevanceReviewFactory,
    complete_workflow_result_factory: WorkflowResultFactory,
) -> None:
    result = DecisionEngine().evaluate(
        complete_workflow_result_factory(
            evidence_review=evidence_review_factory(
                claims=[
                    claim_finding_factory(
                        ClaimStatus.UNCLEAR,
                        ClaimImportance.MEDIUM,
                    )
                ],
                missing_context=["Fictional methodology detail"],
            ),
            relevance_review=relevance_review_factory(50, 40),
        )
    )

    assert result.decision is ReviewDecision.REVISE
    assert all(finding.target_decision is ReviewDecision.REVISE for finding in result.findings)


def test_claim_and_risk_reasons_are_aggregated(
    claim_finding_factory: ClaimFindingFactory,
    evidence_review_factory: EvidenceReviewFactory,
    risk_finding_factory: RiskFindingFactory,
    risk_review_factory: RiskReviewFactory,
    complete_workflow_result_factory: WorkflowResultFactory,
) -> None:
    claims = [
        claim_finding_factory(
            ClaimStatus.UNSUPPORTED,
            ClaimImportance.HIGH,
            f"Fictional unsupported claim {index}",
        )
        for index in range(3)
    ] + [
        claim_finding_factory(
            ClaimStatus.CONTRADICTED,
            ClaimImportance.HIGH,
            f"Fictional contradicted claim {index}",
        )
        for index in range(2)
    ]
    risks = [risk_finding_factory(RiskSeverity.MEDIUM, RiskCategory.OTHER) for _ in range(3)] + [
        risk_finding_factory(RiskSeverity.CRITICAL, RiskCategory.REPUTATIONAL) for _ in range(2)
    ]

    result = DecisionEngine().evaluate(
        complete_workflow_result_factory(
            evidence_review=evidence_review_factory(claims=claims),
            risk_review=risk_review_factory(findings=risks),
        )
    )

    assert result.reason_codes.count(DecisionReasonCode.REVISE_UNSUPPORTED_MATERIAL_CLAIM) == 1
    assert result.reason_codes.count(DecisionReasonCode.BLOCK_HIGH_IMPORTANCE_CONTRADICTION) == 1
    assert result.reason_codes.count(DecisionReasonCode.BLOCK_CRITICAL_RISK) == 1
    assert result.reason_codes.count(DecisionReasonCode.REVISE_ACTIONABLE_RISK) == 1
    assert len(result.reason_codes) == len(set(result.reason_codes))


def test_reordering_findings_and_repeated_evaluation_are_deterministic(
    claim_finding_factory: ClaimFindingFactory,
    evidence_review_factory: EvidenceReviewFactory,
    relevance_review_factory: RelevanceReviewFactory,
    risk_finding_factory: RiskFindingFactory,
    risk_review_factory: RiskReviewFactory,
    complete_workflow_result_factory: WorkflowResultFactory,
) -> None:
    claims = [
        claim_finding_factory(ClaimStatus.CONTRADICTED, ClaimImportance.HIGH),
        claim_finding_factory(
            ClaimStatus.CONTRADICTED,
            ClaimImportance.MEDIUM,
            "A lower-importance fictional contradiction.",
        ),
        claim_finding_factory(
            ClaimStatus.UNSUPPORTED,
            ClaimImportance.MEDIUM,
            "A second fictional claim.",
        ),
        claim_finding_factory(
            ClaimStatus.UNCLEAR,
            ClaimImportance.HIGH,
            "A third fictional claim.",
        ),
    ]
    risks = [
        risk_finding_factory(RiskSeverity.CRITICAL, RiskCategory.CONFIDENTIALITY),
        risk_finding_factory(RiskSeverity.MEDIUM, RiskCategory.REPUTATIONAL),
    ]
    first_workflow = complete_workflow_result_factory(
        evidence_review=evidence_review_factory(
            claims=claims,
            missing_context=["Fictional supporting detail"],
        ),
        relevance_review=relevance_review_factory(40, 59),
        risk_review=risk_review_factory(findings=risks),
    )
    second_workflow = complete_workflow_result_factory(
        evidence_review=evidence_review_factory(
            claims=list(reversed(claims)),
            missing_context=["Fictional supporting detail"],
        ),
        relevance_review=relevance_review_factory(40, 59),
        risk_review=risk_review_factory(findings=list(reversed(risks))),
    )
    first_before = first_workflow.model_dump()
    engine = DecisionEngine()

    first_result = engine.evaluate(first_workflow)
    repeated_result = engine.evaluate(first_workflow)
    reordered_result = engine.evaluate(second_workflow)

    assert first_result == repeated_result == reordered_result
    assert first_workflow.model_dump() == first_before
    assert first_result.reason_codes == [
        DecisionReasonCode.BLOCK_HIGH_IMPORTANCE_CONTRADICTION,
        DecisionReasonCode.BLOCK_CRITICAL_RISK,
        DecisionReasonCode.BLOCK_HIGH_CONFIDENTIALITY_RISK,
        DecisionReasonCode.REVISE_OTHER_CONTRADICTION,
        DecisionReasonCode.REVISE_UNSUPPORTED_MATERIAL_CLAIM,
        DecisionReasonCode.REVISE_UNCLEAR_MATERIAL_CLAIM,
        DecisionReasonCode.REVISE_PARTIAL_RELEVANCE,
        DecisionReasonCode.REVISE_LOW_PERSONALIZATION,
        DecisionReasonCode.REVISE_ACTIONABLE_RISK,
        DecisionReasonCode.REVISE_MISSING_CONTEXT,
    ]


def test_messages_are_stable_and_ignore_ai_wording(
    claim_finding_factory: ClaimFindingFactory,
    evidence_review_factory: EvidenceReviewFactory,
    relevance_review_factory: RelevanceReviewFactory,
    risk_finding_factory: RiskFindingFactory,
    risk_review_factory: RiskReviewFactory,
    complete_workflow_result_factory: WorkflowResultFactory,
) -> None:
    ai_text = "FICTIONAL-AI-EXPLANATION-SHOULD-NOT-APPEAR"
    workflow_result = complete_workflow_result_factory(
        evidence_review=evidence_review_factory(
            claims=[
                claim_finding_factory(
                    ClaimStatus.CONTRADICTED,
                    ClaimImportance.HIGH,
                    ai_text,
                    ai_text,
                )
            ],
            summary=ai_text,
        ),
        relevance_review=relevance_review_factory(39, 59, summary=ai_text),
        risk_review=risk_review_factory(
            findings=[
                risk_finding_factory(
                    RiskSeverity.CRITICAL,
                    RiskCategory.REPUTATIONAL,
                    ai_text,
                )
            ],
            summary=ai_text,
        ),
    )

    result = DecisionEngine().evaluate(workflow_result)

    assert all(finding.message for finding in result.findings)
    assert all(ai_text not in finding.message for finding in result.findings)


def test_decision_finding_rejects_pass_target_and_pass_code() -> None:
    with pytest.raises(ValidationError):
        DecisionFinding(
            code=DecisionReasonCode.BLOCK_LOW_RELEVANCE,
            target_decision=ReviewDecision.PASS,
            message="A decision finding cannot target pass.",
            source=ReviewerName.RELEVANCE,
        )
    with pytest.raises(ValidationError):
        DecisionFinding(
            code=DecisionReasonCode.PASS_QUALITY_GATE_CLEAR,
            target_decision=ReviewDecision.REVISE,
            message="The pass reason cannot be a negative finding.",
            source=ReviewerName.RELEVANCE,
        )


def test_decision_result_enforces_decision_invariants(
    complete_workflow_result_factory: WorkflowResultFactory,
    relevance_review_factory: RelevanceReviewFactory,
) -> None:
    engine = DecisionEngine()
    blocking_finding = engine.evaluate(
        complete_workflow_result_factory(relevance_review=relevance_review_factory(39, 60))
    ).findings[0]
    revision_finding = engine.evaluate(
        complete_workflow_result_factory(relevance_review=relevance_review_factory(40, 60))
    ).findings[0]

    with pytest.raises(ValidationError):
        DecisionResult(decision=ReviewDecision.BLOCK, findings=[revision_finding])
    with pytest.raises(ValidationError):
        DecisionResult(decision=ReviewDecision.REVISE, findings=[blocking_finding])
    with pytest.raises(ValidationError):
        DecisionResult(
            decision=ReviewDecision.PASS,
            findings=[revision_finding],
            pass_reason_code=DecisionReasonCode.PASS_QUALITY_GATE_CLEAR,
        )
    with pytest.raises(ValidationError):
        DecisionResult(decision=ReviewDecision.PASS)
    with pytest.raises(ValidationError, match="duplicate"):
        DecisionResult(
            decision=ReviewDecision.BLOCK,
            findings=[blocking_finding, blocking_finding],
        )

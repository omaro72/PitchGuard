from collections.abc import Callable
from typing import cast

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import ReviewApplicationServices
from app.config import Settings
from app.decision import DecisionFinding, DecisionReasonCode, DecisionResult
from app.decision.engine import DecisionEngine
from app.main import create_app
from app.providers.errors import ProviderOutputValidationError
from app.providers.ollama import OllamaProvider
from app.schemas import (
    AnalysisStatus,
    EvidenceReview,
    RelevanceReview,
    ReviewDecision,
    ReviewerError,
    ReviewerName,
    ReviewRequest,
    RiskReview,
)
from app.workflow import ReviewWorkflow, ReviewWorkflowPolicy, ReviewWorkflowResult
from tests.workflow.conftest import FakeReviewer


class FakeProvider:
    def __init__(self) -> None:
        self.close_count = 0

    async def close(self) -> None:
        self.close_count += 1


class FakeWorkflow:
    def __init__(self, outcome: ReviewWorkflowResult | Exception) -> None:
        self._outcome = outcome
        self.call_count = 0
        self.requests: list[ReviewRequest] = []

    async def run(self, request: ReviewRequest) -> ReviewWorkflowResult:
        self.call_count += 1
        self.requests.append(request)
        if isinstance(self._outcome, Exception):
            raise self._outcome
        return self._outcome


class FakeDecisionEngine:
    def __init__(self, result: DecisionResult) -> None:
        self._result = result
        self.call_count = 0
        self.workflow_results: list[ReviewWorkflowResult] = []

    def evaluate(self, workflow_result: ReviewWorkflowResult) -> DecisionResult:
        self.call_count += 1
        self.workflow_results.append(workflow_result)
        return self._result


class FakeServiceFactory:
    def __init__(self, services: ReviewApplicationServices) -> None:
        self._services = services
        self.call_count = 0
        self.settings: list[Settings] = []

    def __call__(self, settings: Settings) -> ReviewApplicationServices:
        self.call_count += 1
        self.settings.append(settings)
        return self._services


def valid_request_body() -> dict[str, object]:
    return {
        "campaign": {
            "company_name": "Fictional Research",
            "announcement": "A fictional workplace study is ready for publication.",
            "target_audience": "Workplace technology readers",
        },
        "evidence": [
            {
                "id": "E1",
                "source": "Fictional internal study",
                "content": "A study of 120 fictional users found 22% less administrative time.",
            }
        ],
        "journalist": {
            "name": "Alex Morgan",
            "publication": "Example News",
            "beat": "Workplace technology and privacy",
            "recent_coverage": [
                {
                    "id": "C1",
                    "title": "Privacy in workplace software",
                    "summary": "A fictional article about privacy in workplace tools.",
                }
            ],
        },
        "pitch": (
            "Hello Alex, our fictional study found 22% less administrative time. "
            "Would you like the fictional report?"
        ),
    }


def complete_workflow_result() -> ReviewWorkflowResult:
    return ReviewWorkflowResult(
        evidence_review=EvidenceReview(
            claims=[],
            summary="The fictional claims match the supplied evidence.",
            missing_context=[],
        ),
        relevance_review=RelevanceReview(
            relevance_score=84,
            personalization_score=71,
            summary="The fictional pitch matches the supplied journalist profile.",
            matched_topics=["workplace technology"],
            mismatches=[],
            missing_context=[],
        ),
        risk_review=RiskReview(
            findings=[],
            summary="No material risk was found in the fictional pitch.",
            missing_context=[],
        ),
    )


def partial_workflow_result() -> ReviewWorkflowResult:
    complete_result = complete_workflow_result()
    return ReviewWorkflowResult(
        evidence_review=complete_result.evidence_review,
        relevance_review=None,
        risk_review=complete_result.risk_review,
        errors=[
            ReviewerError(
                reviewer=ReviewerName.RELEVANCE,
                code="provider_timeout",
                message="The relevance reviewer could not complete the review.",
                retryable=True,
            )
        ],
    )


def revise_decision() -> DecisionResult:
    return DecisionResult(
        decision=ReviewDecision.REVISE,
        findings=[
            DecisionFinding(
                code=DecisionReasonCode.REVISE_LOW_PERSONALIZATION,
                target_decision=ReviewDecision.REVISE,
                message="Pitch personalization is below the required threshold: 45/100.",
                source=ReviewerName.RELEVANCE,
            )
        ],
    )


def build_test_application(
    workflow_outcome: ReviewWorkflowResult | Exception,
) -> tuple[
    Callable[[], TestClient],
    FakeProvider,
    FakeWorkflow,
    FakeDecisionEngine,
    FakeServiceFactory,
]:
    provider = FakeProvider()
    workflow = FakeWorkflow(workflow_outcome)
    decision_engine = FakeDecisionEngine(revise_decision())
    services = ReviewApplicationServices(
        provider=cast(OllamaProvider, provider),
        workflow=cast(ReviewWorkflow, workflow),
        decision_engine=cast(DecisionEngine, decision_engine),
    )
    service_factory = FakeServiceFactory(services)
    application = create_app(
        Settings(_env_file=None),
        review_services_factory=service_factory,
    )
    return (
        lambda: TestClient(application),
        provider,
        workflow,
        decision_engine,
        service_factory,
    )


def test_complete_review_returns_deterministic_decision_and_all_outputs() -> None:
    workflow_result = complete_workflow_result()
    client_factory, _, workflow, decision_engine, _ = build_test_application(workflow_result)

    with client_factory() as client:
        response = client.post("/api/v1/reviews", json=valid_request_body())

    assert response.status_code == 200
    assert workflow.call_count == 1
    assert decision_engine.call_count == 1
    assert decision_engine.workflow_results == [workflow_result]
    assert response.json() == {
        "analysis_status": AnalysisStatus.COMPLETE,
        "decision": "REVISE",
        "decision_reasons": ["Pitch personalization is below the required threshold: 45/100."],
        "evidence_review": workflow_result.evidence_review.model_dump(mode="json"),
        "relevance_review": workflow_result.relevance_review.model_dump(mode="json"),
        "risk_review": workflow_result.risk_review.model_dump(mode="json"),
        "errors": [],
    }


def test_partial_review_returns_service_unavailable_without_a_decision() -> None:
    workflow_result = partial_workflow_result()
    client_factory, _, workflow, decision_engine, _ = build_test_application(workflow_result)

    with client_factory() as client:
        response = client.post("/api/v1/reviews", json=valid_request_body())

    body = response.json()
    assert response.status_code == 503
    assert workflow.call_count == 1
    assert decision_engine.call_count == 0
    assert body["analysis_status"] == "ERROR"
    assert body["decision"] is None
    assert body["decision_reasons"] == []
    assert body["evidence_review"] == workflow_result.evidence_review.model_dump(mode="json")
    assert body["relevance_review"] is None
    assert body["risk_review"] == workflow_result.risk_review.model_dump(mode="json")
    assert body["errors"] == [
        {
            "reviewer": "RELEVANCE",
            "code": "provider_timeout",
            "message": "The relevance reviewer could not complete the review.",
            "retryable": True,
        }
    ]


def test_invalid_request_returns_unprocessable_entity_without_running_workflow() -> None:
    client_factory, _, workflow, decision_engine, _ = build_test_application(
        complete_workflow_result()
    )
    invalid_body = valid_request_body()
    invalid_body.pop("pitch")

    with client_factory() as client:
        response = client.post("/api/v1/reviews", json=invalid_body)

    assert response.status_code == 422
    assert workflow.call_count == 0
    assert decision_engine.call_count == 0


def test_application_reuses_services_and_closes_provider_on_shutdown() -> None:
    client_factory, provider, workflow, _, service_factory = build_test_application(
        complete_workflow_result()
    )

    with client_factory() as client:
        first_response = client.post("/api/v1/reviews", json=valid_request_body())
        second_response = client.post("/api/v1/reviews", json=valid_request_body())
        assert provider.close_count == 0

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert service_factory.call_count == 1
    assert workflow.call_count == 2
    assert provider.close_count == 1


def test_expected_provider_failure_reaches_safe_partial_response() -> None:
    complete_result = complete_workflow_result()
    raw_model_output = "confidential raw model output"
    full_prompt = "confidential full system prompt"
    internal_response_body = "confidential internal Ollama response body"
    try:
        raise ProviderOutputValidationError() from ValueError(
            f"{raw_model_output} {full_prompt} {internal_response_body}"
        )
    except ProviderOutputValidationError as provider_error:
        workflow = ReviewWorkflow(
            FakeReviewer[EvidenceReview]([provider_error]),
            FakeReviewer([complete_result.relevance_review]),
            FakeReviewer([complete_result.risk_review]),
            ReviewWorkflowPolicy(max_attempts=1),
        )

    provider = FakeProvider()
    decision_engine = FakeDecisionEngine(revise_decision())
    services = ReviewApplicationServices(
        provider=cast(OllamaProvider, provider),
        workflow=workflow,
        decision_engine=cast(DecisionEngine, decision_engine),
    )
    application = create_app(
        Settings(_env_file=None),
        review_services_factory=lambda _: services,
    )
    request_body = valid_request_body()

    with TestClient(application) as client:
        response = client.post("/api/v1/reviews", json=request_body)

    body = response.json()
    response_text = response.text
    assert response.status_code == 503
    assert body["analysis_status"] == "ERROR"
    assert body["decision"] is None
    assert body["evidence_review"] is None
    assert body["relevance_review"] is not None
    assert body["risk_review"] is not None
    assert body["errors"] == [
        {
            "reviewer": "EVIDENCE",
            "code": "provider_output_validation_error",
            "message": "The AI returned an invalid response.",
            "retryable": True,
        }
    ]
    assert decision_engine.call_count == 0
    assert raw_model_output not in response_text
    assert full_prompt not in response_text
    assert internal_response_body not in response_text
    assert str(request_body["pitch"]) not in response_text
    evidence = cast(list[dict[str, object]], request_body["evidence"])
    assert str(evidence[0]["content"]) not in response_text
    assert "Traceback" not in response_text
    assert "http://localhost:11434" not in response_text
    assert "qwen3:8b" not in response_text


def test_unexpected_exception_is_reraised_without_becoming_a_reviewer_error() -> None:
    sensitive_pitch = "Private fictional acquisition details must stay confidential."
    programming_error = RuntimeError(
        f"Unexpected reviewer wiring failure while processing: {sensitive_pitch}"
    )
    client_factory, _, workflow, decision_engine, _ = build_test_application(programming_error)
    request_body = valid_request_body()
    request_body["pitch"] = sensitive_pitch

    with (
        client_factory() as client,
        pytest.raises(RuntimeError, match="Unexpected reviewer wiring failure"),
    ):
        client.post("/api/v1/reviews", json=request_body)

    assert workflow.call_count == 1
    assert decision_engine.call_count == 0


def test_review_endpoint_has_structured_openapi_documentation() -> None:
    client_factory, _, _, _, _ = build_test_application(complete_workflow_result())

    with client_factory() as client:
        operation = client.get("/openapi.json").json()["paths"]["/api/v1/reviews"]["post"]

    request_schema = operation["requestBody"]["content"]["application/json"]["schema"]
    success_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    failure_schema = operation["responses"]["503"]["content"]["application/json"]["schema"]
    assert operation["summary"] == "Review a PR pitch"
    assert operation["tags"] == ["reviews"]
    assert operation["description"]
    assert request_schema["$ref"].endswith("/ReviewRequest")
    assert success_schema["$ref"].endswith("/ReviewResponse")
    assert failure_schema["$ref"].endswith("/ReviewResponse")

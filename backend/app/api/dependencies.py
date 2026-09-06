from dataclasses import dataclass

from fastapi import Request

from app.config import Settings
from app.decision import DecisionEngine
from app.providers.ollama import OllamaProvider
from app.reviewers import ClaimEvidenceReviewer, JournalistRelevanceReviewer, PRRiskReviewer
from app.workflow import ReviewWorkflow


@dataclass(frozen=True, slots=True)
class ReviewApplicationServices:
    provider: OllamaProvider
    workflow: ReviewWorkflow
    decision_engine: DecisionEngine


def create_review_services(settings: Settings) -> ReviewApplicationServices:
    provider = OllamaProvider(settings)
    workflow = ReviewWorkflow(
        evidence_reviewer=ClaimEvidenceReviewer(provider),
        relevance_reviewer=JournalistRelevanceReviewer(provider),
        risk_reviewer=PRRiskReviewer(provider),
    )
    return ReviewApplicationServices(
        provider=provider,
        workflow=workflow,
        decision_engine=DecisionEngine(),
    )


def get_review_services(request: Request) -> ReviewApplicationServices:
    return request.app.state.review_services

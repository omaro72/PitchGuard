from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.dependencies import ReviewApplicationServices, get_review_services
from app.decision import DecisionResult
from app.schemas import AnalysisStatus, ReviewRequest, ReviewResponse
from app.workflow import ReviewWorkflowResult

router = APIRouter(prefix="/reviews", tags=["reviews"])


def build_review_response(
    workflow_result: ReviewWorkflowResult,
    decision_result: DecisionResult | None,
) -> ReviewResponse:
    if workflow_result.is_complete:
        if decision_result is None:
            raise ValueError("A complete workflow result requires a decision result")
        decision_reasons = decision_result.reasons
        if decision_result.pass_reason is not None:
            decision_reasons = [decision_result.pass_reason]
        return ReviewResponse(
            analysis_status=AnalysisStatus.COMPLETE,
            decision=decision_result.decision,
            decision_reasons=decision_reasons,
            evidence_review=workflow_result.evidence_review,
            relevance_review=workflow_result.relevance_review,
            risk_review=workflow_result.risk_review,
            errors=[],
        )

    if decision_result is not None:
        raise ValueError("An incomplete workflow result cannot have a decision result")
    return ReviewResponse(
        analysis_status=AnalysisStatus.ERROR,
        decision=None,
        decision_reasons=[],
        evidence_review=workflow_result.evidence_review,
        relevance_review=workflow_result.relevance_review,
        risk_review=workflow_result.risk_review,
        errors=workflow_result.errors,
    )


@router.post(
    "",
    response_model=ReviewResponse,
    summary="Review a PR pitch",
    description=(
        "Runs the three structured PitchGuard reviewers and applies deterministic "
        "application decision rules when every review completes."
    ),
    response_description="A complete PitchGuard review and deterministic decision.",
    responses={
        503: {
            "model": ReviewResponse,
            "description": "One or more reviewers could not complete safely.",
        }
    },
)
async def create_review(
    review_request: ReviewRequest,
    services: Annotated[ReviewApplicationServices, Depends(get_review_services)],
) -> ReviewResponse | JSONResponse:
    workflow_result = await services.workflow.run(review_request)
    if not workflow_result.is_complete:
        response = build_review_response(workflow_result, decision_result=None)
        return JSONResponse(
            status_code=503,
            content=response.model_dump(mode="json"),
        )

    decision_result = services.decision_engine.evaluate(workflow_result)
    return build_review_response(workflow_result, decision_result)

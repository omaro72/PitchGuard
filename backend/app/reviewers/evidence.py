from app.prompts import ACTIVE_PROMPTS, PromptDefinition, load_prompt
from app.providers.base import GenerationOptions, StructuredGenerationProvider
from app.reviewers.input_builder import build_evidence_input
from app.reviewers.validation import validate_evidence_result
from app.schemas import EvidenceReview, ReviewRequest

_PROMPT_DEFINITION = next(
    definition for definition in ACTIVE_PROMPTS if definition.reviewer == "evidence_reviewer"
)
_GENERATION_OPTIONS = GenerationOptions(temperature=0.0, max_output_tokens=4_096)


class ClaimEvidenceReviewer:
    prompt_definition: PromptDefinition = _PROMPT_DEFINITION

    def __init__(self, provider: StructuredGenerationProvider) -> None:
        self._provider = provider

    async def review(self, request: ReviewRequest) -> EvidenceReview:
        result = await self._provider.generate_structured(
            system_prompt=load_prompt(self.prompt_definition.prompt_id),
            user_prompt=build_evidence_input(request),
            response_model=EvidenceReview,
            options=_GENERATION_OPTIONS,
        )
        validate_evidence_result(result, request)
        return result

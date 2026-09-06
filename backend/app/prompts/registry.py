from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class PromptDefinition:
    reviewer: str
    prompt_id: str
    version: int
    filename: str
    output_model_name: str


ACTIVE_PROMPTS = (
    PromptDefinition(
        reviewer="evidence_reviewer",
        prompt_id="evidence-reviewer-v1",
        version=1,
        filename="evidence_reviewer_v1.md",
        output_model_name="EvidenceReview",
    ),
    PromptDefinition(
        reviewer="relevance_reviewer",
        prompt_id="relevance-reviewer-v1",
        version=1,
        filename="relevance_reviewer_v1.md",
        output_model_name="RelevanceReview",
    ),
    PromptDefinition(
        reviewer="risk_reviewer",
        prompt_id="risk-reviewer-v1",
        version=1,
        filename="risk_reviewer_v1.md",
        output_model_name="RiskReview",
    ),
)

_PROMPTS_BY_ID: Mapping[str, PromptDefinition] = MappingProxyType(
    {definition.prompt_id: definition for definition in ACTIVE_PROMPTS}
)
_TEMPLATE_DIRECTORY = Path(__file__).resolve().parent / "templates"


def load_prompt(prompt_id: str) -> str:
    try:
        definition = _PROMPTS_BY_ID[prompt_id]
    except KeyError as error:
        raise KeyError(f"Unknown prompt ID: {prompt_id}") from error

    path = _TEMPLATE_DIRECTORY / definition.filename
    try:
        prompt_text = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"Registered prompt template is missing: {definition.filename}"
        ) from error

    if not prompt_text.strip():
        raise ValueError(f"Registered prompt template is empty: {definition.filename}")

    return prompt_text

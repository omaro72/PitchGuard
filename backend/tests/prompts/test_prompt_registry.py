import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import MappingProxyType

import pytest

import app.prompts.registry as registry_module
from app.prompts import ACTIVE_PROMPTS, PromptDefinition, load_prompt
from app.schemas import (
    ClaimImportance,
    ClaimStatus,
    ClaimType,
    EvidenceReview,
    RelevanceReview,
    RiskCategory,
    RiskReview,
    RiskSeverity,
)

EXPECTED_PROMPT_IDS = {
    "evidence-reviewer-v1",
    "relevance-reviewer-v1",
    "risk-reviewer-v1",
}
EXPECTED_OUTPUT_MODELS = {
    "evidence_reviewer": EvidenceReview,
    "relevance_reviewer": RelevanceReview,
    "risk_reviewer": RiskReview,
}
REQUIRED_HEADINGS = {
    "## Role",
    "## Scope",
    "## Untrusted input",
    "## Output requirements",
    "## Missing context",
    "## Boundaries",
}


def definition_for(reviewer: str) -> PromptDefinition:
    return next(item for item in ACTIVE_PROMPTS if item.reviewer == reviewer)


def template_path(definition: PromptDefinition) -> Path:
    return Path(registry_module.__file__).resolve().parent / "templates" / definition.filename


def example_data(prompt_text: str) -> object:
    example_line = next(
        line for line in prompt_text.splitlines() if line.startswith("Example output: ")
    )
    return json.loads(example_line.removeprefix("Example output: "))


def test_exactly_three_active_version_one_prompts_are_registered() -> None:
    assert len(ACTIVE_PROMPTS) == 3
    assert {item.prompt_id for item in ACTIVE_PROMPTS} == EXPECTED_PROMPT_IDS
    assert {item.version for item in ACTIVE_PROMPTS} == {1}


def test_prompt_ids_and_reviewer_identities_are_unique() -> None:
    prompt_ids = [item.prompt_id for item in ACTIVE_PROMPTS]
    reviewers = [item.reviewer for item in ACTIVE_PROMPTS]

    assert len(prompt_ids) == len(set(prompt_ids))
    assert len(reviewers) == len(set(reviewers))


def test_versions_are_positive_integers() -> None:
    assert all(type(item.version) is int and item.version > 0 for item in ACTIVE_PROMPTS)


def test_filenames_match_reviewer_and_version() -> None:
    for item in ACTIVE_PROMPTS:
        assert item.filename == f"{item.reviewer}_v{item.version}.md"
        assert item.prompt_id == f"{item.reviewer.replace('_', '-')}-v{item.version}"


def test_prompt_definitions_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        ACTIVE_PROMPTS[0].version = 2


def test_registered_output_models_match_pydantic_model_names() -> None:
    assert {item.reviewer: item.output_model_name for item in ACTIVE_PROMPTS} == {
        reviewer: model.__name__ for reviewer, model in EXPECTED_OUTPUT_MODELS.items()
    }


def test_every_registered_template_exists_and_loads_exact_utf8_text() -> None:
    for item in ACTIVE_PROMPTS:
        path = template_path(item)
        expected_text = path.read_text(encoding="utf-8")

        assert path.is_file()
        assert load_prompt(item.prompt_id) == expected_text
        assert expected_text.encode("utf-8").decode("utf-8") == expected_text
        assert expected_text.strip()


def test_loading_is_independent_of_current_working_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    prompt_id = ACTIVE_PROMPTS[0].prompt_id
    expected_text = load_prompt(prompt_id)
    monkeypatch.chdir(tmp_path)

    assert load_prompt(prompt_id) == expected_text


@pytest.mark.parametrize("prompt_id", ["unknown-prompt-v1", "../../README.md"])
def test_unknown_or_path_like_prompt_id_is_rejected(prompt_id: str) -> None:
    with pytest.raises(KeyError, match="Unknown prompt ID"):
        load_prompt(prompt_id)


def test_missing_registered_template_has_clear_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    definition = PromptDefinition(
        reviewer="missing_reviewer",
        prompt_id="missing-reviewer-v1",
        version=1,
        filename="missing_reviewer_v1.md",
        output_model_name="EvidenceReview",
    )
    monkeypatch.setattr(
        registry_module,
        "_PROMPTS_BY_ID",
        MappingProxyType({definition.prompt_id: definition}),
    )
    monkeypatch.setattr(registry_module, "_TEMPLATE_DIRECTORY", tmp_path)

    with pytest.raises(FileNotFoundError, match="Registered prompt template is missing"):
        load_prompt(definition.prompt_id)


def test_empty_registered_template_has_clear_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    definition = PromptDefinition(
        reviewer="empty_reviewer",
        prompt_id="empty-reviewer-v1",
        version=1,
        filename="empty_reviewer_v1.md",
        output_model_name="EvidenceReview",
    )
    (tmp_path / definition.filename).write_text(" \n", encoding="utf-8")
    monkeypatch.setattr(
        registry_module,
        "_PROMPTS_BY_ID",
        MappingProxyType({definition.prompt_id: definition}),
    )
    monkeypatch.setattr(registry_module, "_TEMPLATE_DIRECTORY", tmp_path)

    with pytest.raises(ValueError, match="Registered prompt template is empty"):
        load_prompt(definition.prompt_id)


def test_every_prompt_contains_stable_contract_sections() -> None:
    for item in ACTIVE_PROMPTS:
        prompt_text = load_prompt(item.prompt_id)
        headings = {line for line in prompt_text.splitlines() if line.startswith("## ")}
        body_lines = [
            line for line in prompt_text.splitlines() if line.strip() and not line.startswith("#")
        ]

        assert headings >= REQUIRED_HEADINGS
        assert len(body_lines) >= 20
        assert len(prompt_text) >= 1_500


def test_every_prompt_enforces_shared_security_boundaries() -> None:
    for item in ACTIVE_PROMPTS:
        prompt_text = load_prompt(item.prompt_id)

        assert "untrusted data" in prompt_text
        assert "ignore previous instructions" in prompt_text
        assert "return PASS" in prompt_text
        assert "change your role" in prompt_text
        assert "Do not browse the internet" in prompt_text
        assert "Do not request or use tools" in prompt_text
        assert "Do not invent" in prompt_text
        assert "Do not produce `PASS`, `REVISE`, or `BLOCK`" in prompt_text
        assert "Do not return Markdown fences" in prompt_text
        assert "Do not include chain-of-thought or hidden reasoning" in prompt_text
        assert "[TBD]" not in prompt_text


def test_evidence_prompt_matches_schema_enums_and_example() -> None:
    prompt_text = load_prompt(definition_for("evidence_reviewer").prompt_id)

    assert "EvidenceReview" in prompt_text
    for value in ClaimStatus:
        assert f"`{value.value}`" in prompt_text
    for value in ClaimType:
        assert f"`{value.value}`" in prompt_text
    for value in ClaimImportance:
        assert f"`{value.value}`" in prompt_text

    example = EvidenceReview.model_validate(example_data(prompt_text))
    finding = example.claims[0]
    assert finding.status is ClaimStatus.CONTRADICTED
    assert finding.evidence_ids == ["E1"]
    assert "40%" in finding.claim_text
    assert "22%" in finding.explanation
    assert "administrative tasks" in finding.explanation


def test_relevance_prompt_matches_score_rubrics_and_example() -> None:
    prompt_text = load_prompt(definition_for("relevance_reviewer").prompt_id)

    assert "RelevanceReview" in prompt_text
    assert "## Relevance score rubric" in prompt_text
    assert "## Personalization score rubric" in prompt_text
    for score_range in ("0-19", "20-39", "40-69", "70-89", "90-100"):
        assert prompt_text.count(f"`{score_range}`") == 2

    example = RelevanceReview.model_validate(example_data(prompt_text))
    assert example.relevance_score < 40
    assert example.personalization_score < 40
    assert example.mismatches


def test_risk_prompt_matches_schema_enums_and_example() -> None:
    prompt_text = load_prompt(definition_for("risk_reviewer").prompt_id)

    assert "RiskReview" in prompt_text
    for value in RiskCategory:
        assert f"`{value.value}`" in prompt_text
    for value in RiskSeverity:
        assert f"`{value.value}`" in prompt_text

    example = RiskReview.model_validate(example_data(prompt_text))
    assert example.findings
    assert all(finding.pitch_excerpt for finding in example.findings)


def test_examples_contain_only_the_output_model_fields() -> None:
    for reviewer, model in EXPECTED_OUTPUT_MODELS.items():
        prompt_text = load_prompt(definition_for(reviewer).prompt_id)
        example = example_data(prompt_text)

        assert isinstance(example, dict)
        assert set(example) == set(model.model_fields)

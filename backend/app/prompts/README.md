# PitchGuard reviewer prompts

This directory contains the versioned system prompts for PitchGuard's three focused AI reviewers. The prompts define reviewer behavior only. Independent reviewer execution is implemented in `app/reviewers`, the fixed concurrent workflow is implemented in `app/workflow`, and deterministic decisions are implemented separately in `app/decision`.

## Active prompts

| Reviewer | Prompt ID | File | Pydantic output model |
| --- | --- | --- | --- |
| Claim and Evidence Reviewer | `evidence-reviewer-v1` | `templates/evidence_reviewer_v1.md` | `EvidenceReview` |
| Journalist Relevance Reviewer | `relevance-reviewer-v1` | `templates/relevance_reviewer_v1.md` | `RelevanceReview` |
| PR Risk Reviewer | `risk-reviewer-v1` | `templates/risk_reviewer_v1.md` | `RiskReview` |

The Evidence Reviewer identifies factual claims and compares them only with supplied evidence. The Relevance Reviewer assesses campaign fit and supported personalization using the supplied journalist context. The Risk Reviewer identifies communication, credibility, confidentiality, and reputational risks in the submitted pitch.

## Naming and versioning

A prompt ID uses `<reviewer-name>-v<integer>`. Its file uses the same reviewer name with underscores: `<reviewer_name>_v<integer>.md`. The registry version, prompt ID, and filename must agree.

Version 1 is the first testable behavior. After a version is used in a recorded evaluation, do not silently change its behavior. A meaningful change to responsibilities, safety rules, scoring, classification rubrics, or the output contract requires a new immutable integer version and a new file, such as `evidence_reviewer_v2.md`. A typographical correction that cannot affect behavior may remain in the existing version, but it must remain visible in Git history. Never replace an older version to hide an unsuccessful evaluation. Keep evaluated versions until an explicit cleanup decision is made.

Evaluate a new or changed prompt before making it active. Structural tests catch missing contracts and schema mismatches, but live evaluation is needed later to assess model behavior across representative safe, unsafe, ambiguous, and adversarial inputs.

## Loading prompts

`load_prompt(prompt_id)` accepts only a registered prompt ID. It resolves the registered filename relative to the prompt package, reads it as UTF-8, and rejects unknown IDs, missing files, and empty files. It returns the file text unchanged. The current backend runs directly from its source tree and is not configured as a distributable wheel; if packaging is introduced later, these Markdown templates must be included as package data.

Campaign and journalist data are not interpolated into system-prompt files. The reviewer input builder places the relevant data in a separate JSON user message. This separation keeps stable instructions distinct from untrusted content and prevents user-controlled values from selecting files or changing the registered system prompt.

## Security and validation

Each prompt treats every submitted value as untrusted data, ignores embedded instructions, forbids tools and browsing, and limits conclusions to supplied information. These instructions reduce risk but cannot make prompt injection impossible. Restricted model capabilities, structured-output enforcement, Pydantic validation, bounded failure handling, and human review are also required.

Ollama structured output supplies the corresponding Pydantic JSON schema, and the provider validates the returned JSON as that model. Prompt text and schema enforcement complement each other; a prompt request alone does not guarantee valid or safe output.

The reviewers report focused findings only. They never choose `PASS`, `REVISE`, or `BLOCK`. The Python-controlled workflow gathers their results, and the deterministic decision engine accepts only a complete workflow result before applying application-owned rules.

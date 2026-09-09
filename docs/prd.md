# PitchGuard MVP product requirements

> **Status: Complete for v0.1.0.** The requirements in the MVP scope below are implemented. Live-model benchmarking and automatic pitch revision are outside the completed scope.

## Problem

PR professionals can use AI to draft outreach quickly, but fluent text can contain unsupported claims, weak journalist targeting, superficial personalization, inappropriate language, or sensitive information. Sending such a pitch can damage journalist relationships and the reputation of an agency or client.

## Intended user

The primary user is a PR professional who wants a reviewable quality check before manually sending a pitch to a journalist.

## MVP objective

Provide a small, local, human-in-the-loop workflow that evaluates a pasted draft pitch against pasted campaign evidence and journalist context. Three focused AI reviewers return structured findings. Deterministic Python code calculates the final `PASS`, `REVISE`, or `BLOCK` recommendation only after all reviews complete successfully.

## Included features

- **Implemented:** Manual campaign, evidence, journalist, recent-coverage, and pitch inputs
- **Implemented:** Claim and evidence review
- **Implemented:** Journalist relevance and personalization review
- **Implemented:** Tone, language, confidentiality, and reputational risk review
- **Implemented:** Pydantic validation for API data and reviewer output
- **Implemented:** Additional semantic validation of evidence references, excerpts, duplicate findings, and conflicting findings
- **Implemented:** A fixed sequential reviewer workflow with bounded retries and timeouts
- **Implemented:** Deterministic `BLOCK`, `REVISE`, and `PASS` rules
- **Implemented:** A validated `POST /api/v1/reviews` endpoint
- **Implemented:** Safe `503` responses with partial results and no final decision after incomplete analysis
- **Implemented:** A responsive manual-input frontend and explainable report
- **Implemented:** Backend and frontend automated tests
- **Implemented:** Three fictional deterministic evaluation cases and eight fictional manual scenarios
- **Implemented:** Optional local Docker Compose startup for the frontend, backend, Ollama, and model download

## Explicit non-goals

The completed MVP does not include:

- automatic pitch rewriting;
- a database or long-term campaign history;
- PDF or other file upload;
- authentication or billing;
- cloud deployment or production operations;
- journalist database access or automatic web scraping;
- email, SMS, or WhatsApp delivery;
- translation or language detection; or
- fully autonomous outreach.

## Implemented inputs

1. Company name
2. Announcement
3. Target audience
4. Zero to 10 evidence items with an ID, source, content, and confidentiality flag
5. Journalist name
6. Publication
7. Coverage focus, stored in the API field `beat`
8. Zero to 10 recent-coverage items with an ID, title, summary, optional date, and optional URL
9. Draft pitch from 50 to 6,000 characters

All values are treated as untrusted input. Text embedded in these values must not be followed as instructions or treated as overriding system instructions.

## Implemented outputs

- Analysis status: `COMPLETE` or `ERROR`
- Final decision for complete analysis: `PASS`, `REVISE`, or `BLOCK`
- Human-readable decision reasons
- Claim classifications and referenced evidence IDs
- Journalist relevance and personalization scores
- Matched topics, mismatches, and missing context
- PR risk categories, severities, explanations, and recommendations
- Safe reviewer errors and any successful partial results when analysis is incomplete

## Human-in-the-loop requirement

PitchGuard provides decision support, not autonomous outreach or a factual guarantee. It never contacts a journalist. A human must inspect the findings and approve any pitch before use.

## Failure behavior

If request validation fails, Ollama is unavailable, a request times out, or a reviewer response is empty, malformed, schema-invalid, or semantically invalid, the analysis does not silently pass. Expected operational failures become typed reviewer errors. The workflow continues to later reviewers when safe, preserves successful partial results, returns `analysis_status = ERROR` with HTTP 503, and supplies no final decision. Unexpected programming errors and cancellation still propagate.

## Acceptance criteria

- Input and reviewer schemas reject invalid data.
- The three reviewers use separate versioned prompts and structured output.
- Reviewer responses cannot reference nonexistent evidence or nonexistent pitch excerpts.
- The reviewer order is Claim and Evidence, Journalist Relevance, then PR Risk.
- Only a complete workflow reaches the deterministic decision engine.
- Decision precedence is `BLOCK > REVISE > PASS`.
- Threshold boundaries are covered by automated tests.
- Normal automated tests do not require Ollama or network access.
- The frontend renders complete reports, partial errors, validation failures, and network failures.
- Backend lint, formatting, and tests pass.
- Frontend tests, lint, type checking, and production build pass.
- Docker Compose configuration and application image builds pass.

## Finalized MVP decisions

Thresholds, input limits, language support, model selection, retry and timeout defaults, testing, container packaging, and licensing are recorded in `docs/project-decisions.md`.

## Work outside v0.1.0

- **Optional stretch goal:** Evidence-bounded Revision Agent
- **Optional stretch goal:** Representative live-model evaluation with defined metrics and acceptance thresholds

These items are not unfinished MVP requirements, and no implementation is claimed.

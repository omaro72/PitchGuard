# AI-assisted development log

This log records meaningful AI-assisted development tasks without implying that generated work was accepted without review.

## 2026-09-07 — Ollama grammar compatibility fix

### Goal

Diagnose and fix the shared `provider_response_error` returned by all three live Ollama reviewers.

### Instructions given to the AI coding tool

Explain the failure in beginner-friendly terms, verify the local services and configured model, reproduce the error without exposing submitted content or raw model output, apply a focused fix when supported by evidence, and provide practical local-running guidance.

### Generated changes reviewed

The coding agent inspected the provider call, safe exception mapping, reviewer schemas, workflow path, Ollama configuration, and installed model state. It compared a minimal structured request with a real fictional reviewer request and isolated the incompatible JSON Schema keyword. Human developer review remains required.

### Problems or incorrect assumptions found

- Ollama, the backend, and `qwen3:8b` were installed and reachable, so service availability was not the cause.
- A minimal structured response succeeded, while each real reviewer received HTTP 400 because Ollama could not parse the generated grammar.
- The failure was triggered by large `maxLength` constraints in the Pydantic JSON Schema sent to Ollama.
- After the grammar failure was removed, one reviewer completed in 42.5 seconds, but the three concurrent `qwen3:8b` reviewers exceeded the workflow timeout on CPU-only execution.

### Corrections made

- Removed `maxLength` keywords only from the provider-specific schema passed to Ollama.
- Preserved all Pydantic response validation, including the original maximum lengths, after generation.
- Added regression tests for recursive schema cleanup and post-generation length rejection.
- Added README instructions for installing the default model and using the smaller `qwen3:4b` model on slower CPU-only hardware.

### Verification performed

- The new regression test failed before the provider fix and passed afterward.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed for 58 Python files.
- `uv run pytest` passed: 297 tests passed and one live-Ollama test was skipped by default.
- A minimal live structured Ollama request passed.
- A real Claim and Evidence review using fictional data passed after the fix.
- A full three-reviewer request using `qwen3:8b` reached generation but returned `provider_timeout_error` on the current CPU-only execution path.

### Remaining limitations

- `qwen3:8b` is too slow for the current concurrent timeout on this machine when running entirely on the CPU.
- `qwen3:4b` is the recommended local development alternative but has not yet been evaluated for PitchGuard quality.
- Live-model evaluation metrics and acceptance thresholds remain `[TBD]`.

## 2026-09-07 — Fictional manual test scenarios

### Goal

Give a developer without PR-sector experience copy-ready fictional inputs for manually exercising varied PitchGuard outcomes and safety behavior.

### Instructions given to the AI coding tool

Create a project folder containing separate Markdown scenarios with campaign, evidence, journalist, recent coverage, and pitch fields; keep the data fictional; cover varied review outcomes; and explain a beginner-friendly alternative to the PR term `beat`.

### Generated changes reviewed

The coding agent reviewed the current form fields, Pydantic request limits, evidence and coverage ID rules, deterministic decision thresholds, risk categories, and English-only MVP decision. It reviewed each scenario for internal consistency, fictional data, copy-ready field values, and a clearly qualified expected outcome. Human developer review remains required.

### Problems or incorrect assumptions found

- The PR term `beat` may be unclear to users outside the industry.
- Existing automated JSON fixtures are useful for deterministic tests but are not formatted for manual copying into the frontend.
- Live model scores and classifications can vary, so a scenario must not present its expected signals as recorded results.

### Corrections made

- Used `Beat / topics covered` in every scenario while preserving the current backend field name.
- Added eight independent scenarios spanning supported claims, unsupported and contradicted claims, wrong targeting, generic personalization, confidentiality, promotional language, and prompt injection.
- Marked every person, organization, publication, fact, and URL as fictional and every outcome as an expectation.

### Verification performed

- Confirmed that all eight Markdown files contain the required campaign, evidence, journalist, recent-coverage, pitch, and expected-signal sections.
- Checked IDs, required text lengths, optional empty lists, and reserved `example.test` URLs against the current request contract.

### Remaining limitations

- The scenarios have not been run against live Ollama and contain no claimed evaluation results.
- Live-model wording, scores, classifications, and non-deterministic outcomes may vary.

## 2026-09-07 — Finalized MVP decisions

### Goal

Finalize the MVP decision thresholds, request limits, language support, frontend testing tools, and license while preserving existing claim, risk, workflow, and product-scope choices.

### Instructions given to the AI coding tool

Inspect existing code and documentation for unfinished or conflicting decisions; keep the established deterministic policy; enforce the specified request limits in Pydantic and mirror them in the form; support and evaluate English only without rejecting Unicode; add focused mocked-fetch frontend tests; add an MIT license; document the decisions; run all checks; and create one focused commit only after review.

### Generated changes reviewed

The coding agent inspected the decision policy and boundary tests, Pydantic request models, form controls, report and API client, CI workflow, package manifests, PRD, README, and active `[TBD]` entries. It reviewed the added schema-boundary and component tests, dependency changes, license text, decision record, and resulting diff. Human developer review remains required.

### Problems or incorrect assumptions found

- The decision thresholds and required boundary tests were already implemented correctly and did not need a new policy layer.
- Several backend request limits and matching form attributes conflicted with the finalized values.
- No frontend test setup existed.
- Current Vitest and Vite packages require Node 24 type definitions, matching the project's Node 24 prerequisite.
- Vite reported that TypeScript path resolution is built in, so an initially installed helper package was unnecessary.
- Character-by-character input in the first payload test exceeded the default test timeout.

### Corrections made

- Preserved the existing decision engine and its `BLOCK > REVISE > PASS` precedence.
- Applied the finalized input limits in backend schemas and matching browser attributes.
- Added Unicode-aware boundary tests and retained unique ID, URL, claim, and risk validation.
- Added Vitest, React Testing Library, `user-event`, `jsdom`, mocked-fetch component tests, and a CI test step.
- Removed the redundant path-resolution package and used Vite's native setting.
- Used direct input change events for the payload test while retaining `user-event` for user interactions.
- Added the MIT license and a concise MVP decisions document, then resolved the related README and PRD placeholders.

### Verification performed

- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed for 58 Python files.
- `uv run pytest` passed: 295 tests passed and the existing live-Ollama test was skipped.
- `npm run test` passed: 9 frontend tests.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `npm run build` passed and prerendered the root route.

### Remaining limitations

- Live-Ollama evaluation metrics, acceptance thresholds, and representative baseline results remain `[TBD]`.
- Frontend tests use `jsdom`; full browser and accessibility audits have not been added.
- The Revision Agent remains an optional stretch goal.

## 2026-09-07 — Fictional review evaluation fixtures

### Goal

Add concise fictional `PASS`, `REVISE`, and `BLOCK` cases that validate real data contracts and deterministic review behavior without Ollama, network access, or real personal data.

### Instructions given to the AI coding tool

Reuse the current request, reviewer-output, workflow, and decision models; store readable JSON fixtures with mocked outputs and stable expectations; use existing fake-provider infrastructure; test the real reviewers, concurrent workflow, semantic validation, and deterministic decision engine; document the deterministic command; and keep live Ollama evaluation optional and outside CI.

### Generated changes reviewed

The coding agent inspected the repository rules, PRD, Pydantic schemas, reviewer validators, provider test doubles, workflow, decision policy and reason codes, current test layout, and evaluation documentation. It reviewed every fictional request, evidence reference, pitch excerpt, score range, expected category, and reason code. Human developer review remains required.

### Problems or incorrect assumptions found

- The root fixture and evaluation documents still described all evaluation data as future work.
- The existing `RecordingProvider` supports one typed result, so each real reviewer needs its own provider instance when a full fixture case is executed.
- A passing `DecisionResult` exposes `PASS_QUALITY_GATE_CLEAR` through `pass_reason_code`, while blocking and revision reasons are exposed through `reason_codes`.
- Exact AI wording would be unstable for a future live evaluation and should not become a deterministic expectation.

### Corrections made

- Added three explicitly fictional JSON fixtures containing valid requests, schema-valid mocked reviewer outputs, expected decisions and reason codes, and stable claim, risk, and score expectations.
- Reused one existing `RecordingProvider` per real reviewer and ran all three reviewers through the real concurrent workflow and decision engine.
- Compared decision codes as sets so fixture array order is not part of the test contract.
- Added a small validated loader with clear failures for malformed JSON and schema-invalid fixture data.
- Updated the README, PRD, fixture guidance, and evaluation guidance to separate implemented deterministic cases from planned optional live-model evaluation.

### Verification performed

- `uv run pytest tests/evaluation` passed: 6 tests.
- `uv run pytest` passed: 282 tests and one skipped opt-in Ollama integration test.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed for 58 Python files.
- No frontend source, dependency, or configuration changed, so frontend checks were not rerun.
- No live Ollama, internet, or other external service was used.

### Remaining limitations

- Live Ollama evaluation remains optional and is not implemented or recorded.
- The deterministic dataset currently contains three baseline cases; wrong-target, invented-statistic, mass-outreach, and prompt-injection cases remain possible future additions.
- Evaluation metrics and acceptance thresholds remain `[TBD: evaluation metrics and acceptance thresholds]`.

## 2026-09-07 — Safe AI failure handling

### Goal

Harden the existing Ollama-to-frontend error path so unavailable services, timeouts, server failures, missing models, invalid structured output, and semantically invalid reviewer results fail closed without losing successful partial reviews.

### Instructions given to the AI coding tool

Extend the existing provider and reviewer exception architecture; retain bounded retry behavior; preserve cancellation and unexpected programming errors; return structured `503` responses with no decision for incomplete workflows; keep sensitive prompts, content, model output, configuration, response bodies, and stack traces out of API responses; and verify the backend and frontend without adding services or dependencies.

### Generated changes reviewed

The coding agent traced the provider, reviewer validation, concurrent workflow, decision boundary, API response mapper, frontend report, and existing tests. It reviewed stable error codes, retryability, model-response parsing, semantic validation, partial-result preservation, cancellation cleanup, public messages, and API serialization. Human developer review remains required.

### Problems or incorrect assumptions found

- The model-not-found message included the configured model name, which is an environment value and should not reach the client.
- Provider messages exposed implementation-specific Ollama and HTTP details even though the frontend only needs short recovery guidance.
- The API caught every exception only to log its type and re-raise it, adding no behavior while widening the error-handling surface.
- Malformed JSON and schema-invalid JSON shared coverage under one broad test name, making the two required cases harder to audit.
- No frontend test framework is configured.

### Corrections made

- Preserved the existing provider exception classes, stable codes, retry flags, and internal status codes while replacing their public messages with short safe text.
- Removed the model name from `ProviderModelNotFoundError` and kept that failure non-retryable.
- Kept empty, malformed, and schema-invalid output under the existing `provider_output_validation_error` code because they share the same safe handling and retry policy.
- Removed the unnecessary broad API exception catch so programming errors and cancellation continue to propagate normally.
- Added focused regression coverage for malformed JSON, schema-invalid JSON, safe model-not-found handling, server failures, semantic reviewer failures, partial API results, sensitive-data exclusion, retry limits, and the incomplete-workflow decision boundary.

### Verification performed

- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed.
- `uv run pytest` passed: 276 tests and one skipped opt-in Ollama integration test.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `npm run build` passed and prerendered the root route.
- No live Ollama, internet, or other external service was used by the normal test suite.

### Remaining limitations

- The live Ollama integration test remains opt-in and was not run.
- The frontend has no automated component test framework; its existing partial-result rendering compiled successfully but was not re-exercised in a browser for this task.
- Live-model quality and response time remain unverified.

## 2026-09-07 — Frontend pitch review form and report

### Goal

Build the first usable manual-input interface for the existing review API and render complete, partial, validation-error, and connection-error outcomes without adding product scope or frontend dependencies.

### Instructions given to the AI coding tool

Use the existing Next.js App Router, TypeScript, Tailwind CSS, and public API-base configuration; match the backend request and response fields; provide dynamic evidence and coverage inputs with stable IDs; submit to `POST /api/v1/reviews`; display every reviewer result and safe error; preserve editable form values; and keep the final decision entirely backend-controlled.

### Generated changes reviewed

The coding agent inspected the repository rules, frontend-specific Next.js guidance, installed Next.js 16 documentation, current frontend source, environment configuration, backend Pydantic schemas, review route, Git history, and Codebase Memory coverage. It reviewed the client boundary, request serialization, response-state handling, stable ID generation, browser validation attributes, accessible field structure, complete and partial report rendering, responsive classes, and status documentation. Human developer review remains required.

### Problems or incorrect assumptions found

- No frontend test framework or test command is configured, so adding component tests would have required new tooling outside this task.
- The session exposed no browser surface for interactive visual testing.
- The sandbox initially prevented the Next.js development server from spawning its worker process.
- Next.js development mode regenerated an HTML-comment block in `frontend/AGENTS.md`, conflicting with the repository's zero-comments rule.

### Corrections made

- Kept the page as a Server Component and isolated state, event handlers, and browser fetch behavior in one focused Client Component.
- Used read-only monotonic `E` and `C` IDs so removal never renumbers an existing item or creates a duplicate.
- Converted `422` details to safe field guidance and used generic messages for malformed, server, and network failures.
- Returned structured `503` responses to the report so successful partial results remain visible with no invented decision.
- Reran the development server with approved process access, disabled Next.js agent-file generation, and restored `frontend/AGENTS.md` unchanged.
- Used a temporary local manual-verification harness and removed it after verification.

### Verification performed

- `npm run lint` passed.
- `npm run typecheck` passed.
- `npm run build` passed and prerendered the root route.
- Development-server HTML contained the campaign, evidence, journalist, coverage, pitch, submit, and report-empty-state content.
- A temporary local harness verified the exact `ReviewRequest` payload, complete report rendering, structured partial-error rendering with preserved results, safe `422` feedback, generic server and network failures, and retry controls.
- No live Ollama or external network request was made.

### Remaining limitations

- Interactive browser and viewport testing could not be performed because no browser was available in the session.
- The frontend has no automated component test framework.
- Live-model quality and response time remain unverified.
- The optional Revision Agent and evaluation dataset remain unimplemented.
- Human developer review is still required.

## 2026-09-06 — Main pitch review API endpoint

### Goal

Expose the existing fixed reviewer workflow and deterministic decision engine through one validated FastAPI endpoint without adding product features or requiring a live Ollama service in tests.

### Instructions given to the AI coding tool

Add `POST /api/v1/reviews`; construct shared settings, provider, reviewers, workflow, and decision services during application lifespan; close the owned provider during shutdown; return complete reviews as `200`, expected partial reviews as structured `503` responses, invalid input as FastAPI `422` responses, and unexpected exceptions through normal internal-error handling without logging user content.

### Generated changes reviewed

The coding agent inspected the repository rules, provisional PRD, settings, Ollama provider lifecycle, reviewer constructors, workflow result invariants, decision result invariants, public response schema, existing application factory, backend test conventions, Codebase Memory index coverage, and dirty Git state. It reviewed the dependency container, lifespan wiring, route, explicit response mapper, OpenAPI metadata, fictional fakes, and endpoint tests. Human developer review remains required.

### Problems or incorrect assumptions found

- The API package and product route did not exist, so the test-first focused run failed at import as expected.
- The root README has no dedicated API section, so no request example was added under the task's documentation restriction.
- The first full test run was blocked by restricted access to pytest's Windows temporary directory.
- FastAPI's test client emits an upstream deprecation warning about AnyIO's `BlockingPortal` alias.
- Existing staged, unstaged, and untracked work prevents a safe isolated commit.

### Corrections made

- Added one application-owned service container rather than constructing an Ollama client per request.
- Kept the route responsible only for orchestration calls, explicit response mapping, status selection, and safe error logging.
- Preserved successful reviewer outputs and existing structured workflow errors in `503` responses without invoking the decision engine.
- Reran the full suite outside the restricted sandbox so pytest could use its normal temporary directory.
- Updated only documentation statements made inaccurate by the new API endpoint.

### Verification performed

- `uv run pytest tests/api/test_reviews.py` passed: 6 tests.
- `uv run pytest` passed: 273 tests and one skipped opt-in integration test.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed for 56 Python files.
- No Python type checker is configured.
- No AI, Ollama, internet, or other network call was made.

### Remaining limitations

- The frontend does not call or display the review API yet.
- The normal API path requires a running local Ollama service and the configured model.
- The optional Revision Agent and evaluation dataset remain unimplemented.
- Human developer review is still required.
- No isolated Git commit was created because unrelated changes predated this task.

## 2026-09-06 — Deterministic pitch decision rules

### Goal

Implement a pure Python decision engine that converts one complete reviewer workflow result into `PASS`, `REVISE`, or `BLOCK` without asking an AI model to choose the outcome.

### Instructions given to the AI coding tool

Add an immutable decision policy, fixed reason-code enum, validated finding and result models, a typed incomplete-workflow error, and a synchronous engine covering all declared claim, relevance, personalization, risk, and missing-context rules. Apply `BLOCK` over `REVISE` over `PASS`, aggregate repeated issue types, preserve deterministic finding order, and use only fictional in-memory tests.

### Generated changes reviewed

The coding agent inspected the repository rules, provisional PRD, reviewer schemas and enums, reviewer implementations, complete and partial workflow-result invariants, test fixtures, package configuration, Codebase Memory index, and dirty Git state. It reviewed every policy boundary, rule predicate, fixed message, reviewer source, result invariant, export, factory fixture, and decision test. Human developer review remains required.

### Problems or incorrect assumptions found

- The decision package did not exist, so the test-first focused run failed at import as expected.
- `ReviewWorkflowResult` already requires every missing reviewer result to have a matching structured error, so a missing result without an error cannot be constructed as valid test input.
- The task describes high confidentiality as `HIGH` but also explicitly requests critical confidentiality to produce both confidentiality and critical-risk blockers.
- The task requested docstrings, but the repository's stricter zero-comments rule forbids docstrings.
- The first Ruff run found formatting and import-order issues only.
- Existing staged, unstaged, and untracked work prevents a safe isolated commit.

### Corrections made

- Tested incomplete decisions with valid partial workflow results containing the required matching reviewer error.
- Treated both `HIGH` and `CRITICAL` confidentiality findings as confidentiality blockers; a critical confidentiality finding therefore returns both distinct blocking codes.
- Used descriptive names and focused tests instead of comments or docstrings.
- Applied Ruff's import ordering and formatting changes.
- Chose the first affected reviewer in Evidence, Relevance, Risk order as the source of the single aggregated missing-context finding.
- Updated only documentation statements made inaccurate by the new engine.

### Verification performed

- Tests covered every blocking and revision rule, the passing path, all declared threshold boundaries, valid and invalid custom policies, incomplete workflows, precedence, aggregation, deterministic ordering, repeated evaluation, reordered reviewer findings, stable messages, result invariants, and input immutability.
- The default policy uses relevance boundaries of 40 and 70 and a personalization boundary of 60.
- `uv run ruff format --check .` passed for 50 Python files.
- `uv run ruff check .` passed.
- `uv run pytest tests/decision` passed: 60 tests.
- `uv run pytest` passed: 267 tests and one skipped opt-in integration test.
- No Python type checker is configured.
- No AI, Ollama, internet, or other network call was made.

### Remaining limitations

- The engine is not yet connected to a FastAPI review endpoint or the frontend.
- The public `ReviewResponse` mapping and final report assembly remain unimplemented.
- Current thresholds need evaluation against a representative fictional dataset before they should be changed.
- A `PASS` means only that the supplied information passed the implemented rules; it is not a factual, legal, response, or media-coverage guarantee.
- Human developer review is still required.
- No isolated Git commit was created because unrelated changes predated this task.

## 2026-09-06 — Fixed concurrent reviewer workflow

### Goal

Implement the fixed Python workflow that runs the existing Claim and Evidence, Journalist Relevance, and PR Risk reviewers without adding final pitch decision logic.

### Instructions given to the AI coding tool

Inject the three reviewers, run all of them concurrently for one validated request, apply an immutable bounded timeout and retry policy to each attempt, preserve successful partial results, convert only expected operational failures into structured errors, re-raise programming errors, propagate cancellation, and use fake reviewers for all tests. Do not call Ollama or add endpoints, frontend behavior, decision rules, or external workflow dependencies.

### Generated changes reviewed

The coding agent inspected the repository rules, provisional PRD, current schemas, reviewer interfaces, provider and reviewer exceptions, test conventions, Codebase Memory index, and dirty Git state. It reviewed the new policy, result invariants, identity-based task mapping, centralized retry helper, task cleanup, public exports, fake reviewers, and workflow tests. Human developer review remains required.

### Problems or incorrect assumptions found

- The workflow package did not exist, so the test-first focused run failed at import as expected.
- The task requested optional short docstrings, but the repository's stricter zero-comments rule forbids docstrings.
- The first invariant test used four errors even though the shared schema permits at most three; that prevented the duplicate-reviewer validator from being reached.
- The first Ruff run found formatting and modern generic-syntax issues in the new tests.
- Existing staged, unstaged, and untracked work prevents a safe isolated commit.

### Corrections made

- Used explicit names, focused functions, and tests instead of comments or docstrings.
- Reduced the duplicate-error test to three entries so it tests the intended invariant.
- Applied Ruff formatting and Python 3.14 generic syntax.
- Made final error ordering independent of task completion order: Evidence, Relevance, then Risk.
- Updated only documentation statements made inaccurate by this implementation.

### Verification performed

- Synchronization-event tests confirmed that all three reviewers start concurrently and that completion order cannot mix up their results.
- Tests confirmed complete success, each single-reviewer failure, all-reviewer failure, retry success, retry exhaustion, non-retryable failure, reviewer contract failure, timeout cancellation, programming-error propagation, workflow cancellation, task cleanup, policy bounds, result invariants, request identity, and request immutability.
- `uv run ruff format --check .` passed for 42 Python files.
- `uv run ruff check .` passed.
- `uv run pytest tests/workflow` passed: 26 tests.
- `uv run pytest` passed: 207 tests and one skipped opt-in integration test.
- No Python type checker is configured.
- No Ollama, internet, or other network request was made.

### Remaining limitations

- The workflow gathers reviewer output only; it does not calculate `PASS`, `REVISE`, or `BLOCK`.
- No FastAPI review endpoint or frontend integration exists.
- Live Ollama workflow evaluation and an evaluation dataset remain future tasks.
- Human developer review is still required.
- No isolated Git commit was created because unrelated changes predated this task.

## 2026-09-06 — Specialized PR reviewers

### Goal

Implement the independent Claim and Evidence, Journalist Relevance, and PR Risk reviewers by connecting validated requests, versioned prompts, the provider-independent generation interface, and the existing reviewer-output schemas.

### Instructions given to the AI coding tool

Create three asynchronous reviewer classes with injected providers, deterministic reviewer-specific JSON inputs, fixed generation options, post-Pydantic semantic validation, safe typed contract errors, and fake-provider tests. Do not add orchestration, retries, final decisions, endpoints, frontend work, or live model evaluation.

### Generated changes reviewed

The AI coding agent inspected the Codebase Memory graph, repository rules, PRD, schemas, provider boundary and Ollama implementation, active prompts, prompt registry, tests, package configuration, documentation, and dirty Git state. It created the reviewer package, a deterministic input builder, shared conservative validation helpers, a safe `ReviewerContractError`, three reviewer classes, and a recording test provider. Human developer review remains required.

### Problems or incorrect assumptions found

- The reviewer package did not exist, so the first focused test run failed at import as expected.
- The task suggested optional docstrings, but the repository's zero-comments rule forbids docstrings and takes precedence.
- The first Ruff pass found import ordering, line length, formatting, and an overly broad tuple annotation in new code.
- The README still described all three reviewers as planned and therefore became inaccurate after implementation.
- Existing unrelated staged, unstaged, and untracked work prevents a safe isolated commit.

### Corrections made

- Used descriptive class, method, helper, and test names instead of comments or docstrings.
- Corrected Ruff findings and narrowed the duplicate-claim key annotation to the implemented `ClaimType`.
- Updated only the README and PRD status lines made inaccurate by this task.
- Kept provider failures unchanged and limited contract-error messages to safe fixed text without submitted content.

### Verification performed

- Each reviewer loaded its registered active prompt and called the injected provider exactly once with the expected Pydantic model and deterministic generation options.
- Input tests confirmed that Evidence receives `campaign`, `evidence`, and `pitch`; Relevance receives `campaign`, `journalist`, and `pitch`; and Risk receives `campaign`, `evidence`, and `pitch`.
- JSON tests covered dates, URLs, confidentiality booleans, non-ASCII text, quotes, line breaks, backslashes, deterministic serialization, and prompt-injection language remaining data.
- Semantic tests covered evidence references, exact normalized excerpts, duplicate findings, relevance-list conflicts, and confidentiality preconditions.
- Provider-exception tests confirmed that the original exception type and instance propagate.
- `uv run ruff format --check .` passed for 35 Python files.
- `uv run ruff check .` passed.
- `uv run pytest tests/reviewers` passed: 44 tests.
- `uv run pytest` passed: 181 tests and one skipped opt-in integration test.
- No Python type checker is configured.
- No Ollama, internet, or other network request was made.

### Remaining limitations

- The reviewers run independently; orchestration, concurrency, retries, final decision rules, and review endpoints remain unimplemented.
- Structural and mocked tests do not establish live-model quality.
- Live reviewer evaluation must wait for orchestration and defined evaluation scenarios.
- No isolated Git commit was created because unrelated changes predated this task.

## 2026-09-06 — Versioned reviewer system prompts

### Goal

Create the first production-ready, versioned system prompts for the Evidence, Relevance, and Risk reviewers, together with a small safe loader and structural tests, without implementing reviewer execution or orchestration.

### Instructions given to the AI coding tool

Write one focused system prompt per reviewer, treat all submitted JSON values as untrusted data, match the existing Pydantic output contracts and enums, use immutable version metadata, prevent user-controlled path loading, document the lifecycle rules, and avoid any live Ollama request.

### Generated changes reviewed

The AI coding agent inspected the Codebase Memory graph, repository rules, PRD, schemas, structured-generation provider, test layout, packaging configuration, and dirty Git state. It created `evidence-reviewer-v1`, `relevance-reviewer-v1`, and `risk-reviewer-v1`, registered their files and Pydantic model names, added a module-relative UTF-8 loader, documented prompt versioning and security boundaries, and added focused tests. Human developer review remains required.

### Problems or incorrect assumptions found

- The prompt package did not exist, so the first focused test run failed at import as expected.
- The instruction to name `PASS`, `REVISE`, and `BLOCK` for prompt-injection defense had to be reconciled with the rule that they must never be offered as reviewer outputs.
- The first Ruff checks found an outdated `typing.Mapping` import, one reversed subset assertion, and formatting differences in the new tests.
- Existing unrelated staged, unstaged, and untracked work prevents a safe isolated commit.

### Corrections made

- Mentioned the three decision values only as forbidden embedded instructions and forbidden reviewer outputs.
- Used the exact implemented fields, enum values, evidence-reference invariant, and score bounds in the prompts and their validated examples.
- Replaced the outdated import, simplified the subset assertion, and applied the required test formatting.
- Kept prompt selection limited to registered IDs and kept user JSON separate from system-prompt loading.

### Verification performed

- The initial focused test run confirmed the expected missing-package failure before implementation.
- All three compact example outputs were parsed as JSON and validated against `EvidenceReview`, `RelevanceReview`, or `RiskReview` in automated tests.
- Registry tests covered immutable definitions, exact active IDs, version and filename alignment, UTF-8 loading, working-directory independence, missing and empty templates, and rejection of unknown or path-like IDs.
- Prompt-contract tests covered stable sections, current enums and score rubrics, untrusted embedded instructions, browsing and invention prohibitions, final-decision boundaries, and the absence of active `[TBD]` placeholders.
- No live Ollama evaluation or external request was performed.

### Remaining limitations

- The tests verify structure and schema alignment, not the quality or consistency of model behavior.
- Live prompt evaluation must wait for reviewer classes, JSON input builders, orchestration, and representative evaluation cases.
- Reviewer execution, retry behavior, final decision rules, and review API endpoints remain unimplemented.
- No isolated Git commit was created because unrelated changes predated this task.

## 2026-09-06 — Ollama provider interface

### Goal

Create a small provider-independent structured-generation boundary and a local Ollama implementation without adding reviewers, prompts, orchestration, decisions, or API routes.

### Instructions given to the AI coding tool

Define a generic typed provider protocol, immutable generation options, safe provider errors, an injectable asynchronous Ollama provider, mocked unit tests, and a skipped-by-default local integration test.

### Generated changes reviewed

The AI coding agent inspected the Codebase Memory graph, repository rules, PRD, validated settings, Pydantic schemas, test conventions, dependency files, and the installed Ollama client source and signatures. It added the provider package, official Ollama and HTTPX dependencies, timeout configuration, unit and optional integration tests, public exports, and small factual documentation updates. Human developer review remains required.

### Problems or incorrect assumptions found

- The official `ollama` and direct `httpx` packages were not yet installed.
- The repository's zero-comments rule overrides the task's suggestion to add optional docstrings.
- The initial injected-client assignment used truthiness and could replace a valid false-like test client.
- The first Ruff run found one unused import.
- Existing unrelated staged, unstaged, and untracked work prevents a safe isolated commit.

### Corrections made

- Added only the official `ollama` client and direct `httpx` dependency, then refreshed `uv.lock`.
- Used descriptive types, methods, errors, and tests instead of comments or docstrings.
- Changed client selection to an explicit `is not None` ownership check.
- Removed the unused import and reran all required checks.
- Kept Ollama-specific request fields inside `OllamaProvider`; the public interface uses `max_output_tokens` rather than `num_predict`.

### Verification performed

- Python 3.14.3, Pydantic 2.13.5, Pydantic Settings 2.15.0, Ollama 0.6.2, and HTTPX 0.28.1 were confirmed.
- `uv run ruff format --check .` passed for 14 Python files.
- `uv run ruff check .` passed.
- `uv run pytest` passed: 119 tests and one skipped integration test.
- Mocked tests verified request construction, JSON-schema output, response validation, safe error mapping, exception chaining, and client ownership.
- The normal test suite made no Ollama or internet request.
- No Python type checker is configured.

### Remaining limitations

- The opt-in live Ollama integration test was skipped and not run against a local model.
- The provider does not retry, pull models, implement reviewer prompts, or participate in FastAPI lifecycle management.
- Reviewer orchestration must later decide retry policy and translate provider failures into incomplete analyses.
- No isolated Git commit was created because unrelated changes predated this task.

## 2026-09-06 — Validated environment configuration

### Goal

Centralize and validate the backend and frontend environment configuration without adding product behavior or contacting Ollama.

### Instructions given to the AI coding tool

Use Pydantic Settings for backend configuration, add a cached settings factory, configure restrictive CORS behavior, create a small immutable frontend environment module, preserve safe local defaults, and fail early for invalid values.

### Generated changes reviewed

The AI coding agent inspected the Codebase Memory graph, repository rules, provisional PRD, installed Next.js documentation, dependency configuration, environment examples, CI workflow, Git ignore rules, and existing uncommitted work. It added backend and frontend configuration modules, backend tests, FastAPI CORS integration, CI environment configuration, and small factual documentation updates. Human developer review remains required.

### Problems or incorrect assumptions found

- The original backend CORS example used a single string instead of the required JSON list syntax.
- The first implementation briefly used unnecessary runtime mutation to connect Pydantic validators.
- Sandboxed test and build processes could not access the normal Windows temporary directory or spawn Next.js workers.
- The repository already contained unrelated staged, unstaged, and untracked work, so an isolated commit was not safe.

### Corrections made

- Updated `CORS_ORIGINS` to use JSON list syntax.
- Replaced the runtime validator mutation with standard Pydantic v2 `field_validator` decorators.
- Re-ran blocked checks with approved access to the existing uv cache, temporary directory, and Next.js worker processes.
- Kept Ollama values in the backend and exposed only the non-secret backend base URL through the frontend.
- Limited provisional CORS methods to `GET` and `POST`, headers to `Content-Type`, and disabled credentials.

### Verification performed

- `uv run ruff format --check .` passed for seven Python files.
- `uv run ruff check .` passed.
- `uv run pytest` passed: 85 tests.
- `uv run python -c "from app.main import app; print(app.title)"` imported the application with valid defaults.
- An application import with an invalid `OLLAMA_BASE_URL` failed with a Pydantic validation error.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `npm run build` passed with the default frontend URL.
- `npm run build` passed with a valid frontend URL override.
- A build with an invalid frontend protocol failed with a clear `NEXT_PUBLIC_API_BASE_URL` error.
- No Ollama request was made.

### Remaining limitations

- The frontend has no automated test framework, so its invalid-configuration behavior was verified through production builds.
- CORS allows the current health-check `GET` and the immediately planned JSON `POST`; this list must remain aligned with implemented API routes.
- Configuration validates the Ollama URL and model name but does not check whether Ollama is running or whether the model is installed.
- No isolated Git commit was created because unrelated changes predated this task.

## 2026-09-06 — Review data schemas

### Goal

Define the validated data contract for review requests, reviewer outputs, failures, and final responses without implementing review behavior.

### Instructions given to the AI coding tool

Create Pydantic v2 models and direct model tests for the specified fields, enums, limits, ID formats, duplicate detection, claim evidence requirements, and complete-versus-error response invariants.

### Generated changes reviewed

The AI coding agent reviewed the existing backend through the Codebase Memory graph and source configuration, confirmed Pydantic 2.13.5, added `backend/app/schemas.py` and `backend/tests/test_schemas.py`, and inspected their final diff. Human developer review remains required.

### Problems or incorrect assumptions found

- The task suggested optional model docstrings, but the repository requires zero comments and docblocks.
- The first focused test run failed because the schema module intentionally did not exist yet.
- One parameterized test line exceeded the configured Ruff line length.
- The working tree already contained unrelated staged, unstaged, and untracked work, so an isolated task commit was not safe.

### Corrections made

- Used descriptive model and validator names instead of docstrings.
- Implemented the schema module after confirming the expected failing test state.
- Applied Ruff's required line wrapping.
- Limited implementation changes to data contracts and validation; no route, model provider, prompt, reviewer, or decision engine was added.

### Verification performed

- `uv run ruff format --check .` passed.
- `uv run ruff check .` passed.
- `uv run pytest` passed: 51 tests.
- The repository-owned source scan found no comments or docstrings.
- The diff and environment files were reviewed; no secret or Ollama request was added.

### Remaining limitations

- Evidence references are format-checked but are not checked against a request's evidence collection; that belongs to orchestration.
- The schemas define data shape and safety invariants but do not execute reviewers or calculate decisions.
- No isolated Git commit was created because unrelated changes predated this task.

## 2026-09-06 — Zero-comment scaffold cleanup

### Goal

Remove repository-owned code comments and Python docstrings so the scaffold follows the zero-comments development rule without changing behavior.

### Instructions given to the AI coding tool

Find and remove existing code comments and docstrings, keep the system simple, preserve behavior, and verify the backend and frontend.

### Generated changes reviewed

The AI coding agent inspected graph-indexed Python and frontend symbols, scanned repository-owned source and configuration files for comment syntax, and reviewed the resulting diff. Human developer review remains required.

### Problems or incorrect assumptions found

- Python module, class, function, and test docstrings remained from the initial scaffold.
- Generated Next.js configuration contained explanatory comments.
- The root `.gitignore` contained organizational comments.
- The generated frontend agent guidance used HTML comment markers.
- Next.js generates an ignored `next-env.d.ts` file containing framework directives and notices; it is generated build metadata rather than repository-owned source.

### Corrections made

- Removed the Python docstrings.
- Removed comments from the Next.js and ESLint configuration.
- Removed organizational comments from `.gitignore`.
- Consolidated the frontend agent guidance without HTML comment markers.

### Verification performed

- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed for three Python files.
- `uv run pytest` passed: one health endpoint test.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `npm run build` passed and prerendered the root route.
- The final repository-owned source and configuration scan found no comments or docstrings.

### Remaining limitations

- Ignored dependencies and generated build artifacts are outside the zero-comments audit scope.

## 2026-09-06 — Repository scaffolding

### Goal

Create the initial local development scaffold, repository rules, documentation, minimal health endpoint, minimal under-development page, quality tooling, and CI configuration without implementing PitchGuard product behavior.

### Instructions given to the AI coding tool

Inspect and preserve the existing repository; create separate FastAPI and Next.js projects; add the required environment examples, repository guidance, provisional PRD, fixture and evaluation documentation, health test, linting, type checking, build checks, and GitHub Actions workflow; verify all checks; and commit only if verification succeeds.

### Generated changes reviewed

The AI coding agent inspected the repository state and generated scaffold files. It reviewed the resulting source, configuration, dependency manifests, lockfiles, documentation, Git diff, and ignore rules. Human developer review remains required before this commit is relied upon.

### Problems or incorrect assumptions found

- The repository and `main` branch already existed, so Git did not need to be initialized.
- A detailed root README already existed as uncommitted work and needed to be preserved and updated.
- The first `create-next-app` attempt could not access an uncached npm package in the sandbox; the command was retried with approved network access.
- The generated Next.js starter included promotional page content and unused image assets that were outside the requested minimal interface.
- The first pytest run could not import the local `app` package because the project root was absent from pytest's configured import path.
- FastAPI's current test client warned that its HTTPX compatibility path is deprecated in favor of HTTPX2.
- The generated ESLint 9 release emitted an end-of-support warning. ESLint 10 satisfied Next.js's direct peer range but was rejected by transitive Next.js lint plugins.

### Corrections made

- Preserved and updated the existing README rather than replacing it with a shorter provisional document.
- Replaced the generated Next.js page and metadata with PitchGuard-specific under-development content.
- Removed unused starter image assets and the generated frontend README.
- Added explicit repository scope and safety constraints for future coding agents.
- Configured pytest's import path and changed the endpoint test to use HTTPX2's ASGI transport.
- Restored the peer-compatible ESLint 9 line after verifying that ESLint 10 produced an invalid dependency tree.

### Verification performed

- `uv sync --locked --dev` completed with CPython 3.14.3.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed for three Python files.
- `uv run pytest` passed: one health endpoint test.
- `npm ci` completed and reported zero vulnerabilities.
- `npm run lint` passed.
- `npm run typecheck` passed.
- `npm run build` passed and prerendered the root route.
- Repository status, diff hygiene, environment-file exclusions, and secret patterns were reviewed before commit.

### Remaining limitations

- PitchGuard review features are not implemented.
- Local Ollama integration is not implemented or exercised.
- Product thresholds, limits, evaluation metrics, and several UX decisions remain `[TBD]` in the PRD.
- The peer-compatible ESLint 9 package emits an upstream end-of-support warning during installation; moving to ESLint 10 is blocked by current transitive Next.js plugin peer ranges.

---

## Date and task

### Goal

### Instructions given to the AI coding tool

### Generated changes reviewed

### Problems or incorrect assumptions found

### Corrections made

### Verification performed

### Remaining limitations

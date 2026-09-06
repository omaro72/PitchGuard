# PitchGuard provisional product requirements

> **Status: In progress.** This document defines intended MVP behavior. The repository scaffold, health check, review data schemas, validated environment configuration, versioned prompts, structured-generation provider, three independent reviewers, their fixed concurrent workflow, deterministic decision engine, and main review API endpoint are implemented. The product UI remains unimplemented.

## Problem

PR professionals can use AI to draft outreach quickly, but a fluent pitch can contain unsupported claims, poor journalist targeting, superficial personalization, inappropriate language, or sensitive information. Sending such a pitch can damage journalist relationships and the reputation of an agency or client.

## Intended user

The primary intended user is a PR professional who needs a reviewable quality check before manually sending a pitch to a journalist.

## MVP objective

Provide a small, local, human-in-the-loop workflow that evaluates a pasted draft pitch against pasted campaign evidence and journalist context. Specialized AI reviewers will return structured findings, while deterministic Python code will calculate the final `PASS`, `REVISE`, or `BLOCK` recommendation.

## Included features

- Pasted-text inputs for campaign context, evidence, journalist context, recent coverage, and the draft pitch
- Claim and evidence review
- Journalist relevance and personalization review
- Tone, language, confidentiality, and reputational risk review
- **Implemented:** Pydantic validation models for planned API and reviewer data
- **Implemented:** A fixed Python-controlled workflow that runs all three reviewers concurrently and returns complete or partial results
- **Implemented:** Deterministic `BLOCK`, `REVISE`, and `PASS` rules for complete workflow results
- **Implemented:** A validated `POST /api/v1/reviews` response containing an explainable complete report or safe partial results
- **Implemented:** Safe API handling of incomplete, malformed, or timed-out model responses
- Automated tests and a small fictional evaluation dataset

## Explicit non-goals

The MVP will not include:

- a database or long-term campaign management;
- PDF or other file upload;
- authentication or billing;
- deployment configuration;
- journalist database access or automatic web scraping;
- email, SMS, or WhatsApp delivery;
- a production-complete user interface; or
- fully autonomous outreach.

## Planned inputs

1. Campaign or company brief
2. Supporting evidence or verified facts
3. Journalist profile
4. Examples of the journalist's recent coverage
5. Draft PR pitch

All inputs must be treated as untrusted text and must not be allowed to override system instructions.

## Planned outputs

- Overall decision: `PASS`, `REVISE`, or `BLOCK`
- Journalist relevance score
- Personalization score
- Supported, unsupported, contradicted, and unclear claims
- Tone, language, confidentiality, and reputational warnings
- Human-readable explanations and recommended actions
- An optional evidence-bounded revised pitch that is clearly marked for human approval

## Human-in-the-loop requirement

PitchGuard is decision support, not an autonomous sender or a factual guarantee. It must never contact a journalist. A human must inspect the findings and approve any pitch or revision before use.

## Failure behavior

If input validation fails, an AI provider times out, or an AI response is malformed, incomplete, or invalid, the review must remain incomplete. The system must expose the failure and must not silently return `PASS` or manufacture missing findings. Retries must be bounded.

## Unresolved product decisions

- `[TBD: evaluation evidence required before changing the implemented decision thresholds or precedence]`
- `[TBD: maximum input and output sizes]`
- `[TBD: supported languages for the MVP]`
- `[TBD: whether evaluation results require changing the workflow defaults of two attempts, a 0.25-second retry delay, and a 130-second per-attempt timeout]`
- `[TBD: evaluation metrics and acceptance thresholds]`
- `[TBD: whether the Revision Agent is included in the MVP or retained as a stretch goal]`
- `[TBD: how incomplete-review state is represented in the UI]`

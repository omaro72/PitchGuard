# PitchGuard MVP project decisions

> **Status: Final for v0.1.0.**

This document records the product and engineering choices used by the completed local MVP.

## Decision policy

The deterministic Python policy uses these thresholds:

- relevance below 40 produces `BLOCK`;
- relevance from 40 through 69 produces `REVISE`;
- relevance of at least 70 is eligible for `PASS`;
- personalization below 60 produces `REVISE`; and
- claim and risk rules remain unchanged.

The decision precedence is `BLOCK > REVISE > PASS`. These values live in `DecisionPolicy`, not in prompts or frontend code. Boundary tests cover relevance scores 39, 40, 69, and 70 and personalization scores 59 and 60. Changes require matching policy tests and evaluation evidence because a small threshold change can alter whether a pitch is safe to use.

## Request input limits

The API is authoritative. The frontend mirrors limits that browsers can enforce before submission.

| Input | Limit |
| --- | ---: |
| Company name | 120 characters |
| Announcement | 2,000 characters |
| Target audience | 500 characters |
| Evidence items | 10 |
| Evidence source | 300 characters |
| Evidence content | 3,000 characters per item |
| Journalist name | 120 characters |
| Publication | 160 characters |
| Beat | 500 characters |
| Recent coverage items | 10 |
| Coverage title | 300 characters |
| Coverage summary | 1,000 characters per item |
| Pitch | 50 to 6,000 characters |

The limits keep local inference requests bounded while allowing a complete, manually pasted pitch and supporting context. Existing ID uniqueness, ID format, and URL validation remain in force.

The existing reviewer generation budgets remain 4,096 tokens for Claim and Evidence, 2,048 for Journalist Relevance, and 3,072 for PR Risk. The fixed workflow retains two attempts, a 0.25-second retry delay, and a 130-second per-attempt timeout.

The fixed reviewer order is Claim and Evidence, Journalist Relevance, then PR Risk. Reviewers run sequentially so each local inference request receives the available CPU and memory without waiting behind other concurrent requests. Expected reviewer failures do not stop later reviewers, allowing successful partial results to remain available. Cancellation and unexpected programming errors still propagate immediately.

## Language support

English is the only language officially supported and evaluated for the MVP. The interface, prompts, fixtures, and expected AI output remain English. Input accepts normal Unicode text, but the application does not detect, translate, or reject a language based on a guess. Other languages are currently untested and unsupported.

## Local model and configuration

The provider is local Ollama, accessed only by the Python backend through the provider interface. `OLLAMA_MODEL` remains configurable and defaults to `qwen3:4b`. The original `qwen3:8b` default exceeded the configured timeout when three reviews competed for CPU on the tested machine. The smaller default and sequential reviewer workflow favor a portable demonstration on unfamiliar hardware; they do not establish better model quality.

The native development defaults are:

| Setting | Default |
| --- | --- |
| Application environment | `development` |
| Ollama URL | `http://localhost:11434` |
| Ollama model | `qwen3:4b` |
| Provider timeout | 120 seconds |
| Workflow timeout per attempt | 130 seconds |
| Workflow attempts | 2 |
| Retry delay | 0.25 seconds |
| Frontend URL allowed by CORS | `http://localhost:3000` |
| Browser API URL | `http://localhost:8000` |

The workflow timeout is slightly longer than the provider timeout so provider-level failures can be translated into the intended safe error before the workflow guard expires. Environment examples, application defaults, Docker Compose, tests, and active documentation use the same model and endpoint assumptions.

## Frontend testing

Frontend component tests use Vitest, React Testing Library, and `user-event` with a `jsdom` environment. Tests mock `fetch` and never require the FastAPI backend or Ollama. This combination exercises user-visible behavior and the API boundary without adding a browser automation or state-management layer.

## License

PitchGuard uses the MIT License. The full terms are in the repository-root `LICENSE` file.

## Local container packaging

Docker Compose is an optional reviewer-friendly startup path, not a cloud deployment. It runs the frontend, backend, and a pinned multi-architecture Ollama image as separate services. A one-shot service downloads the configurable model, which defaults to `qwen3:4b`, into a persistent Docker volume before the backend starts. The portable default is CPU execution because GPU configuration differs across operating systems and hardware vendors.

Host ports default to 3000 for the frontend and 8000 for the backend and can be overridden when those ports are occupied. Native development remains supported for contributors who want faster edit-and-reload cycles.

## Outside the completed MVP

Representative live-Ollama metrics, acceptance thresholds, and baseline results are not defined or claimed for v0.1.0. The evidence-bounded Revision Agent is also an **Optional stretch goal**. These are future possibilities rather than unresolved requirements for the completed MVP.

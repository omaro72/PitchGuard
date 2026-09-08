# PitchGuard MVP project decisions

This document records the small set of product and engineering choices finalized for the local MVP.

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

## Language support

English is the only language officially supported and evaluated for the MVP. The interface, prompts, fixtures, and expected AI output remain English. Input accepts normal Unicode text, but the application does not detect, translate, or reject a language based on a guess. Other languages are currently untested and unsupported.

## Frontend testing

Frontend component tests use Vitest, React Testing Library, and `user-event` with a `jsdom` environment. Tests mock `fetch` and never require the FastAPI backend or Ollama. This combination exercises user-visible behavior and the API boundary without adding a browser automation or state-management layer.

## License

PitchGuard uses the MIT License. The full terms are in the repository-root `LICENSE` file.

## Intentionally unresolved

- `[TBD: live-Ollama evaluation metrics and acceptance thresholds]`
- `[TBD: representative live-Ollama baseline results]`

The evidence-bounded Revision Agent remains an optional stretch goal and is not part of the MVP.

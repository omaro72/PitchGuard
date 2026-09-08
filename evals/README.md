# Evaluations

Three deterministic cases are implemented in `backend/tests/fixtures/evaluation/`. They use mocked reviewer responses and run through the real reviewers, workflow, and decision engine without Ollama or network access.

Run them from the repository root with:

```bash
cd backend
uv run pytest tests/evaluation
```

Live evaluation against local Ollama remains optional and **Planned**. It must remain excluded from normal tests and CI, evaluate stable properties rather than exact wording, and record the model and prompt version with any real result. No recorded live-evaluation results are included.

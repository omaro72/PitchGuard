# Evaluations

Three deterministic cases are implemented in `backend/tests/fixtures/evaluation/`. They use mocked reviewer responses and run through the real reviewers, workflow, and decision engine without Ollama or network access.

Run them from the repository root with:

```bash
cd backend
uv run pytest tests/evaluation
```

Representative live evaluation against Ollama is **Not included in MVP v0.1.0**. The skipped-by-default integration test checks only that the configured service can return a minimal structured response; it is not a quality benchmark.

If live evaluation is added later, it must remain outside normal tests and CI, assess stable properties rather than exact wording, and record the model, prompt versions, cases, metrics, and acceptance criteria. No live quality result is claimed in this repository.

# Mathingo Backend

FastAPI service backing the Mathingo web application.

Runs as part of the project-wide Docker Compose stack — see the root `README.md`
for setup. Standalone development without Docker is possible with
`uv sync && uv run uvicorn app.main:app --reload`, but a running PostgreSQL
instance is still required.

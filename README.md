# Mathingo

Vzdělávací webová aplikace pro krátké každodenní procvičování vysokoškolské matematiky ve stylu Duolinga.

## Stack

- Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, shadcn/ui, KaTeX
- FastAPI (Python 3.12), Pydantic v2, SQLAlchemy 2.0 (async), Alembic
- PostgreSQL 16
- Docker Compose, nginx, Let's Encrypt
- Hostováno na Contabo Cloud VPS 10

## Lokální spuštění

```bash
cp .env.example .env
# vyplň hodnoty (POSTGRES_PASSWORD, SECRET_KEY, ...)
docker compose up --build
```

Po nastartování stacku jsou dostupné:

- frontend (landing page): <http://localhost:3000>
- backend (Swagger UI): <http://localhost:8000/docs>
- health check: <http://localhost:8000/health>

PostgreSQL běží jen v interní docker síti — z hostu k němu přímý přístup není potřeba.

## Nasazení

Bude doplněno po nasazení.

---

Projekt vzniká jako praktická část bakalářské práce na Vysoké škole ekonomické v Praze.

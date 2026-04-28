# Mathingo — Project Context for Claude Code

> Educational web application for practicing mathematics in the style of Duolingo.
> Built as the practical part of a bachelor's thesis at VŠE Prague.

---

## 1. Project Overview

**What it is:** A gamified web application for short daily practice of university-level
mathematics, modelled on the retention mechanisms of Duolingo (streaks, XP, lesson path).
The MVP is built around the syllabus of the course **4MM101 — Matematika pro informatiky
a statistiky** at Vysoká škola ekonomická v Praze.

**Target user:** A VŠE student (typically 18–23 years old, Czech-speaking) preparing
for the 4MM101 exam. The app is designed for sessions of 5–10 minutes.

**User-facing language:** All UI strings, lesson content, error messages, and emails
are in **Czech**. Code, comments, commits, and internal documentation are in **English**.

**Production URL:** https://mathingo.cz

---

## 2. Tech Stack (fixed — do not propose alternatives)

### Frontend
- **Next.js 15** with the App Router
- **React 19**
- **TypeScript 5.x** (strict mode)
- **Tailwind CSS** for styling — utility-first, no separate CSS files
- **shadcn/ui** for components — components are copied into the repo, not installed
- **KaTeX** for rendering mathematical notation

### Backend
- **FastAPI** (Python 3.12)
- **Pydantic v2** for request/response validation
- **SQLAlchemy 2.0** (async) as ORM
- **Alembic** for database migrations
- **asyncpg** as the PostgreSQL driver

### Database
- **PostgreSQL 16** with `JSONB` support for variable exercise payloads

### Infrastructure
- **Docker Compose** orchestrating: `frontend`, `backend`, `postgres`
- **nginx** as a reverse proxy with TLS termination
- **Let's Encrypt** (Certbot) for TLS certificates
- **Contabo Cloud VPS 10** as the host (Ubuntu LTS, 4 vCPU, 8 GB RAM, 75 GB NVMe)
- **GitHub** for version control and as a backup of the codebase

---

## 3. Repository Structure

```
/
├── CLAUDE.md                 # this file
├── README.md                 # human-facing project description
├── docker-compose.yml        # production orchestration
├── docker-compose.dev.yml    # development overrides
├── .env.example              # template for required env vars (no secrets)
├── .gitignore
│
├── frontend/                 # Next.js application
│   ├── app/                  # App Router pages and layouts
│   ├── components/           # React components (incl. shadcn/ui)
│   ├── lib/                  # client-side utilities
│   ├── public/
│   └── package.json
│
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/              # route handlers grouped by domain
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # business logic
│   │   └── main.py
│   ├── alembic/              # database migrations
│   ├── tests/
│   └── pyproject.toml
│
├── infra/
│   ├── nginx/                # nginx site configs
│   └── scripts/              # deployment helpers
│
└── docs/
    ├── prd.md                # product requirements (functional spec)
    └── decisions/            # architecture decision records (ADR)
```

---

## 4. Coding Conventions

### General
- **Language:** Code, identifiers, comments, commit messages, and PR descriptions in English.
  User-facing strings (UI labels, emails, error messages shown to users) in Czech.
- **Line length:** 100 characters (Python and TypeScript alike).
- **Imports:** Sorted automatically (Ruff for Python, ESLint+Prettier for TS).

### Frontend (TypeScript / React)
- Functional components only; no class components.
- One component per file. File name matches component name (`PascalCase.tsx`).
- Prefer **server components**; use `"use client"` only when interactivity requires it.
- Use **shadcn/ui primitives** before writing a custom component.
- All forms use server actions; do not write manual `fetch()` calls when a server action will do.

### Backend (Python / FastAPI)
- Type hints are mandatory on all function signatures.
- Each route handler lives in `app/api/<domain>.py` (e.g. `app/api/lessons.py`).
- Business logic in `app/services/`, never inside route handlers.
- Pydantic schemas are defined in `app/schemas/`, separate from ORM models.
- Use **async** SQLAlchemy throughout — no sync sessions.

### Commits
- Conventional Commits format: `<type>(<scope>): <subject>`
  - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `infra`
  - Examples: `feat(lessons): add streak calculation`, `fix(auth): expire magic link after 15min`
- Subject in imperative mood ("add", not "added"), max 72 chars.
- Body (optional) explains *why*, not *what*.

### Branching
- `main` is the deployment branch. Anything merged here is deployed.
- Feature work happens on `feat/<slug>` branches; merge via PR with squash.
- Never force-push to `main`.

---

## 5. Hard Constraints (what you must not do)

1. **Never add a new top-level dependency** (npm package, Python package) without
   explicit confirmation from the developer. If a new dependency seems necessary,
   stop and ask.
2. **Never modify or delete an existing Alembic migration** that has been committed.
   Schema changes are made through new migrations only.
3. **Never use browser storage APIs** (`localStorage`, `sessionStorage`, IndexedDB)
   for authentication tokens. Auth tokens go in HTTP-only, `Secure`, `SameSite=Lax` cookies.
4. **Never commit secrets.** API keys, passwords, JWT secrets, and database
   credentials live in `.env` (gitignored). Use `.env.example` to document required vars.
5. **Never delete existing tests.** If a test fails after a legitimate refactor,
   update the test in the same commit and explain why in the commit body.
6. **Never bypass migrations** to alter the production database directly.
7. **Never push directly to `main`** except for trivial documentation fixes —
   use a PR.
8. **Never log personally identifiable information** (email addresses, magic link
   tokens) in plain text. Logs may include user UUIDs only.

---

## 6. Development Workflow

### First-time setup
```bash
cp .env.example .env        # then fill in values
docker compose -f docker-compose.dev.yml up --build
```

### Running locally
- Frontend: `http://localhost:3000`
- Backend (OpenAPI docs): `http://localhost:8000/docs`
- Database: `postgres://localhost:5432/mathingo` (only from inside the network)

### Database migrations
```bash
# create a new migration after changing models/
docker compose exec backend alembic revision --autogenerate -m "add streak table"
# apply migrations
docker compose exec backend alembic upgrade head
```

### Tests
```bash
docker compose exec backend pytest
docker compose exec frontend npm test
```

### Deployment
- Push to `main` triggers CI on GitHub Actions.
- On green CI, the workflow SSHs into the VPS, pulls the latest commit,
  rebuilds containers, and runs migrations.
- Manual rollback: `git revert` the offending commit and push.

---

## 7. Definition of Done

A feature is considered complete when **all** of the following hold:
- The code is written in idiomatic Next.js / FastAPI as described above.
- It is covered by at least one automated test (unit or integration).
- The relevant section of `docs/prd.md` is updated.
- The change is committed with a Conventional Commits message.
- It builds in CI without warnings.
- Manually verified in the local Docker environment.

---

## 8. Out of Scope for the MVP

The following are deliberately **not** part of the initial implementation. Do not
add them unless the developer explicitly requests it:

- Native mobile applications (iOS, Android). The web app must be mobile-friendly
  via responsive design, but no React Native or Capacitor wrapper.
- Offline mode and PWA installability.
- Multi-language UI. Czech only for the MVP.
- Adaptive difficulty / spaced repetition algorithms. The lesson path is static
  in the MVP; smarter sequencing is a post-thesis extension.
- Payment integration. The MVP is fully free.
- Advanced analytics dashboards beyond basic per-user statistics.
- Symbolic math input or full CAS integration. Exercise types in the MVP are
  limited to: `multiple_choice`, `numeric`, `true_false`, `matching`,
  `step_ordering`.

---

## 9. Working Style

- **Plan before you code.** For any non-trivial change, propose a short plan
  (which files, which migrations, which tests) before writing code.
- **Small commits.** Prefer many small, well-described commits over one large one.
- **Ask when unsure.** If a requirement is ambiguous or contradicts existing code,
  pause and ask. Do not guess at intent.
- **Update `docs/prd.md` as you go.** When a feature is implemented, mark its
  status in the PRD and note any deviations from the original spec.

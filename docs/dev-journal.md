# Mathingo — Development Journal

Chronologický záznam vývoje pro účely bakalářské práce.
Jeden záznam = jedna pracovní session s Claude Code.

---

## Session 002 — 2026-04-28 — Project scaffold

- **Prompt ID:** #2 (project scaffold)
- **Iterací plánu:** 1 (plán schválen na první pokus s drobnou korekcí načasování tohoto journal entry)
- **Uživatelských zpráv v session:** 2 (prompt + schválení plánu)
- **Commity:** 8 (poslední `a4aa937` před vyplněním tohoto záznamu)

### Cíl

Minimální běžící stack: Next.js 15 (frontend), FastAPI (backend), Postgres 16,
orchestrované přes Docker Compose. Cílový stav: `docker compose up --build`
rozjede tři služby, `/` ukáže „Mathingo — brzy v provozu", `/health`
reportuje stav app i DB, `/docs` Swagger UI.

### Co fungovalo na první pokus

- Plán schválen v první iteraci, jediná korekce se týkala načasování dev journal.
- Instalace `uv` přes oficiální curl-skript proběhla bez chyby.
- `npx create-next-app@15` s plnou sadou explicitních flagů projel bez interaktivních promptů.
- `uv lock` zresolvoval 35 balíčků za 2 s.
- `docker compose config` validace prošla napoprvé.
- Po opravě jediné chyby (viz níže) celý stack najel a všechny tři služby reportují healthy do 30 s.
- `/health` vrací `{"app":"ok","db":"ok"}`, `/` vrací HTML s `<h1>Mathingo</h1>` + `<p>Brzy v provozu.</p>` a `lang="cs"`, `/docs` vrací Swagger UI s titulkem `Mathingo API - Swagger UI`.

### Co bylo potřeba opravit

1. **NodeSource setup_22.x selhal kvůli expirovanému gh CLI GPG klíči.**
   `apt-get update` uvnitř NodeSource skriptu narazil na chybějící klíč
   z `cli.github.com` repository (nesouvisející side-repo). Fallback z Ubuntu
   noble nainstaloval Node 18.19 bez `npm`. Oprava: refresh keyringu
   (`curl … githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/…`),
   poté `apt purge nodejs`, opětovně NodeSource setup, `apt install nodejs`
   → Node 22.22.2 + npm 10.9.7.
   **Lekce:** stale apt klíče třetích stran blokují instalační skripty
   úplně jiných stacků. Před instalací nového stacku stojí za to zkontrolovat
   `ls /etc/apt/sources.list.d` a refreshnout/ vyřadit problematické sources.

2. **`backend/.dockerignore` vyřazoval `README.md`, hatchling neuměl postavit balíček.**
   První `docker compose up --build` selhal v `uv sync --frozen` s
   `OSError: Readme file does not exist: README.md`. `pyproject.toml` deklaruje
   `readme = "README.md"` a hatchling tu metadata validaci provádí během
   buildu. README ale nebyl v build kontextu — `.dockerignore` ho explicitně
   vylučoval (převzatý reflex z webových projektů, kde README do imageu
   nepatří). Oprava: odstranit jednu řádku z `.dockerignore`. Implementováno
   samostatným `fix(backend)` commitem (`a4aa937`), aby byla chyba i řešení
   viditelné v historii.
   **Lekce:** `.dockerignore` musí respektovat soubory, které build backend
   (hatchling, setuptools…) potřebuje pro metadata. README pro Pythonové
   balíčky není jen dokumentace navenek — je to deklarovaná metadata.

### Rozhodnutí, která stojí za zaznamenání

- **`uv` místo pip** — 10–100× rychlejší instalace, nativní `uv.lock` pro reproducibility, single static binary v Docker builderu.
- **`hatchling` jako build-backend** — umožní `uv sync` udělat editable install projektu, takže `uvicorn app.main:app` najde modul `app` bez ladění `PYTHONPATH`. Alternativa `[tool.uv] package = false` + ENV `PYTHONPATH=/app` byla zamítnuta jako méně standardní.
- **Jeden `docker-compose.yml` zatím** — split na base + `docker-compose.dev.yml` (jak ho předjímá CLAUDE.md repo struktura) odložen na prompt #3, kde poprvé reálně nastane dev↔prod divergence (nginx exposed ven, frontend/backend interní).
- **Multi-stage Dockerfile s `dev`, `builder`, `runner`** — dev staví compose dnes; builder a runner jsou připraveny pro produkční sestavení v #3 bez dalšího refactoringu.
- **Anonymní volume na `/app/.venv` a `/app/node_modules`** — chrání in-image instalace před stínem bind mountu zdrojáku, hot reload funguje bez ztráty deps.
- **`output: "standalone"` v `next.config.ts`** — minimální produkční Next.js image, nutný teď aby runner stage Dockerfile dával smysl v #3.

### Použité verze

| Komponenta | Verze |
|---|---|
| uv | 0.11.8 |
| Node | 22.22.2 |
| npm | 10.9.7 |
| Docker Engine | 29.4.1 |
| Docker Compose | v5.1.3 |
| Next.js | 15.5.15 |
| React | 19.1.0 |
| Tailwind CSS | 4.x (novější než původně očekávané 3.4 — `create-next-app` 15.5 defaultuje na 4) |
| TypeScript | ^5 |
| FastAPI / SQLAlchemy / asyncpg / pydantic / pydantic-settings | viz `backend/uv.lock` |
| Postgres | 16.13 (oficiální `postgres:16` image) |

### Co zbývá doladit v promptu #3

- Rozdělit `docker-compose.yml` na base + dev override (nebo přidat `docker-compose.prod.yml` s nginx + certbot).
- Sundat `ports:` z frontend a backend, publikovat 80/443 na nginx.
- nginx site config v `infra/nginx/` (proxy_pass na frontend:3000 a backend:8000, redirect www → apex).
- Certbot pro Let's Encrypt na `mathingo.cz` + `www.mathingo.cz`.
- `restart: unless-stopped` na všechny služby (zatím vynecháno, ať dev errors selhávají hlasitě).

### Dojem

- Plán-pak-vykonat režim sedl scaffoldovému úkolu dobře. 6 explicitních
  otevřených otázek v plánu šetřilo zpětné iterace — schválení proběhlo
  v jedné odpovědi.
- Granulárních 8 commitů funguje pro pozdější dokumentaci v BP přesně
  jak slíbil prompt: každý commit pokrývá jeden uchopitelný krok a má
  vysvětlující body, takže historie čte sama o sobě.
- Dvě překážky (gh GPG klíč, dockerignore vs hatchling) zabraly dohromady
  pár minut, ale obě byly nečekané. První je hygienická záležitost
  prostředí, druhá je past, která se snadno přenese z jiných stacků
  (frontend `.dockerignore` šablony) bez toho, aby se ověřilo, jestli
  build backend daného jazyka README opravdu nepotřebuje.

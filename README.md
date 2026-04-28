# Mathingo

Vzdělávací webová aplikace pro krátké každodenní procvičování vysokoškolské matematiky ve stylu Duolinga.

## Stack

- Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, shadcn/ui, KaTeX
- FastAPI (Python 3.12), Pydantic v2, SQLAlchemy 2.0 (async), Alembic
- PostgreSQL 16
- Docker Compose, nginx, Let's Encrypt
- Hostováno na Contabo Cloud VPS 10

## Lokální vývoj

```bash
cp .env.example .env
# v .env nastav minimálně:
#   COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml
#   POSTGRES_PASSWORD, SECRET_KEY (a další — viz .env.example)
docker compose up --build
```

Dev override (`docker-compose.dev.yml`) buildí `dev` stage Dockerfilů, vystavuje porty
3000/8000 na host a bind-mountuje zdrojáky pro hot reload.

Po nastartování:

- frontend: <http://localhost:3000>
- backend Swagger: <http://localhost:8000/docs>
- health check: <http://localhost:8000/health>

## Produkční nasazení

Cíl: `https://mathingo.cz` (Contabo Cloud VPS 10), nginx reverse proxy, Let's Encrypt
cert s auto-renewalem.

### Předpoklady

- DNS A pro `mathingo.cz` i `www.mathingo.cz` ukazuje přímo na IP VPS
  (tj. žádný Cloudflare proxy "orange cloud" — buď grey cloud, nebo jiný DNS provider).
- Porty 80 a 443 dostupné z internetu.
- Repozitář naklonovaný v `/root/projects/mathingo`.

### První deploy

1. `cp .env.example .env` a vyplnit. Klíčové hodnoty pro prod:

   ```dotenv
   COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml
   ENVIRONMENT=production
   NEXT_PUBLIC_APP_URL=https://mathingo.cz
   BACKEND_CORS_ORIGINS=https://mathingo.cz
   DOMAIN=mathingo.cz
   LE_EMAIL=<reálný email pro LE expirační varování>
   POSTGRES_PASSWORD=<silné heslo>
   SECRET_KEY=<openssl rand -hex 32>
   DATABASE_URL=postgresql+asyncpg://mathingo:<heslo>@postgres:5432/mathingo
   ```

2. **Bootstrap certu + start stacku** (idempotentní):

   ```bash
   bash infra/certbot/init.sh
   ```

   Při prvním běhu skript:
   - vygeneruje dummy self-signed cert, aby nginx mohl nastartovat,
   - spustí stack (postgres → backend → frontend → nginx),
   - validuje webroot pipeline proti LE **staging** serveru (žádný rate-limit risk),
   - smaže staging i dummy,
   - vystaví ostrý LE cert,
   - reloadne nginx.

   Při dalších bězích (cert už existuje): rovnou exit 0.

3. **Auto-renewal:**

   ```bash
   bash infra/certbot/install-renewal-cron.sh
   ```

   Nainstaluje denní cron (03:00) — `certbot renew` (no-op dokud cert nemá < 30 dní)
   plus `nginx -s reload`. Logy v `/var/log/mathingo-renewal.log`. Identifikační
   sentinel komentář v cron řádku → instalace je idempotentní.

### Update existujícího deploymentu

```bash
git pull
docker compose up -d --build
```

### Co je vystavené ven

Po deploy jen porty **80** a **443** (oba terminované na nginx). Frontend (3000)
a backend (8000) jsou dostupné jen interně přes docker network `mathingo_net`.

---

Projekt vzniká jako praktická část bakalářské práce na Vysoké škole ekonomické v Praze.

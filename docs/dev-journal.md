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

---

## Session 003 — 2026-04-28 — Production deployment behind nginx + Let's Encrypt

- **Prompt ID:** #3 (nginx + Let's Encrypt + compose split)
- **Iterací plánu:** 2 (první plán pauznut na pre-flight nálezu Cloudflare proxy; druhý plán šel po user-side grey-cloudu DNS)
- **Uživatelských zpráv v session:** 4 (prompt + grey-cloud potvrzení + plán schválení; čtvrtá je tato po-deploy review)
- **Commity v session:** 7 plánovaných + 1 fix commit pro `--no-deps`

### Cíl
Aplikace běží produkčně na `https://mathingo.cz`, backend pod `/api/...`, www → apex
redirect, validní LE cert s auto-renewalem, porty 3000/8000 už nejsou venku.
Lokální vývoj musí dál fungovat přes `docker compose up`.

### Co fungovalo na první pokus
- **Pre-flight DNS check zachytil Cloudflare proxy** — `dig` ukázal `172.67.x.x`/
  `104.21.x.x` IP rangy a HTTP odpověď měla `Server: cloudflare` + `CF-RAY`.
  Bez toho by HTTP-01 challenge selhalo na proxy a pravděpodobně bych nasadil
  cert, který browser stejně neviděl. Cena: pět minut + jeden round trip s uživatelem.
- **Compose split** (base + dev override + prod override) prošel napoprvé
  bez build issue. `docker compose -f base -f dev config --quiet` validace OK,
  totéž s prod.
- **nginx Dockerfile build** napoprvé.
- **`/api/` rewrite** přes trailing slash na `proxy_pass http://backend:8000/;` —
  funkční bez jediné změny v `backend/app/`. `/api/health` vrátí stejný JSON jako
  interní `/health` na backendu.
- **HSTS, HTTP→HTTPS redirect, www→apex redirect** — všechno na první pokus.
- **`certbot renew --dry-run`** simulace renewalu prošla na první pokus
  po vystavení ostrého certu: "all simulated renewals succeeded".

### Co bylo potřeba opravit
1. **Cloudflare proxy v cestě.** Pre-flight zjistil, že DNS pro `mathingo.cz`
   vede přes Cloudflare. To by znamenalo: (a) browser vidí CF cert, ne LE cert
   (verifikační test by selhal), (b) webroot challenge přes CF proxy je křehčí.
   Pauznul jsem plánovací fázi, vysvětlil tři možnosti (grey-cloud, DNS-01,
   drop LE), uživatel grey-cloudoval.
   **Lekce:** Pre-flight read-only ověření před produkčním change není přepych —
   DNS realita se může lišit od user mental model "DNS ukazuje na VPS".

2. **`--no-deps` zablokoval webroot challenge.** První spuštění `init.sh`
   selhalo v phase 3 s LE "connection refused" na portu 80. nginx visel
   v restart loopu s `host not found in upstream "backend"` — `docker compose
   up -d --no-deps nginx` nestartne backend, ale nginx config rezolvuje
   `proxy_pass http://backend:8000/;` při config load. Oprava: sundat
   `--no-deps`. compose chain (postgres → backend → frontend → nginx)
   zařídí backend dostupnost před nginx startem. Přidá to ~30 s na cold
   bootstrap, ale je to robustnější. Defenzivnější alternativa (resolver +
   variable v nginx pro late-binding DNS) odložena, protože vyžaduje
   `rewrite ... break;` aby /api/ stripping fungoval s variable proxy_pass.
   **Lekce:** nginx static `proxy_pass` rezolvuje hostnames při config load;
   v Dockeru s `--no-deps` to znamená "upstream musí už existovat".

3. **Backend a frontend image v dev stage cached z prompt #2.** Po prvním
   úspěšném `docker compose up -d` běžel backend s `--reload` a frontend
   s `npm run dev` — Docker reusoval cached `mathingo-backend:latest` /
   `mathingo-frontend:latest`, které byly built z prompt #2 jako dev target.
   Compose s prod override neoznačuje target (defaultuje na poslední stage =
   runner), ale cache se nehnula. Oprava: `docker compose build backend
   frontend` + `docker compose up -d --force-recreate`. Pak backend běží
   `uvicorn app.main:app` bez `--reload`, frontend `node server.js` (Next.js
   standalone).
   **Lekce:** `docker compose build` (bez `--no-cache`) bere z cache i když
   compose definice změnila build target — tagy `<project>-<service>:latest`
   se neliší dev↔prod. Po změně targetu rebuildovat explicitně.

### Rozhodnutí, která stojí za zaznamenání
- **`COMPOSE_FILE` v `.env`** místo Makefile. `docker compose up` (bez `-f`)
  na obou stranách dělá to správné. Nepřidává Make. README a `.env.example`
  dokumentují per-prostředí hodnotu.
- **Initial cert přes webroot s dummy cert bootstrap** (vs. standalone-then-
  reload). Single nginx config, žádný runtime swap konfigů. Dummy cert
  (self-signed, 1 day) jen aby nginx nabootoval; po vystavení ostrého
  certu se dummy smaže a real nahradí. Sentinel `.bootstrap-dummy` chrání
  před nešťastným re-runem na produkci.
- **`--staging` → `delete` → prod cert.** LE staging dry-run validuje celý
  webroot pipeline bez rate-limit risku. Až pak ostrá emise.
- **Auto-renewal: cron na hostu** (vs dedicated service). Standardní pattern,
  transparentní logy v dedicated `/var/log/mathingo-renewal.log`. Sentinel
  komentář `# mathingo:letsencrypt-renewal` v cron řádku dělá installer
  idempotentní.
- **`/api/` rewrite přes trailing slash na `proxy_pass http://backend:8000/`.**
  Žádné změny v `backend/app/`. FastAPI o prefixu neví.
- **Frontend `lib/api.ts`** rozlišuje server-side (Docker DNS na `backend:8000`)
  vs client-side (relativní `/api` přes nginx). Žádný fetch wrapper, žádné
  error handlingu — jen URL resolution.

### Výslovně out of scope této session
- **Firewall (`ufw`).** Aktivace `ufw` z SSH session má historický track-record
  bricknutí serveru. Pro thesis projekt nepotřebný risk: dev porty 3000/8000
  už **nejsou** published z Dockeru (prod override nedeklaruje host ports
  pro frontend/backend), takže ven nejdou. `ss -tlnp | grep -E ':(3000|8000)'`
  vrací prázdno. Aktivace ufw z hostingové konsole je volitelnost na později.
- **Cloudflare proxy.** Po dokončení LE deployment je možné CF znovu zapnout
  v módu "Full (Strict)" (LE cert na originu, CF terminuje TLS s vlastním
  edge cert) pokud bude zájem o CDN/DDoS. Aktuálně žádné CF mezi browser
  a VPS.
- **`restart: unless-stopped`** je v prod override, ale není ověřeno přes
  host reboot. Otestovatelné při příští restartu VPS.

### Použité verze a artefakty
| Komponenta | Verze |
|---|---|
| nginx | 1.27 (Alpine) |
| certbot | image `certbot/certbot:latest` (v3.x) |
| LE cert | issuer C=US, O=Let's Encrypt, CN=E8 |
| Cert validity | 2026-04-28 19:01 UTC → 2026-07-27 19:01 UTC |
| Cron schedule | `0 3 * * *` (denně 03:00) |

### Dojem
- **Pre-flight DNS check** byl jediná věc, která zachránila session od
  potenciálního cert rate-limitu (5 fail/h, 5 cert/domain/týden u LE prod).
  Cena pěti minut.
- Tři postupně odkrývané chyby (CF proxy → `--no-deps` → dev image cache)
  byly každá samostatně rychle opravitelná, ale dohromady ilustrují,
  že každá vrstva (DNS / orchestrace / image cache) má vlastní subtleties,
  které pre-build validace nezachytí. Pro reflexi v BP cenné.
- Granulární commits + per-session journal entry s "co fungovalo /
  co bylo třeba opravit" rozpisem dělají session retrospektivně
  srozumitelnou. Po půl roce (až budu psát thesis writeup) budu vědět,
  co rozhodlo a proč.

---

## Session 004 — 2026-04-28 — Datový model a první migrace

- **Prompt ID:** #4 (data model + initial migration)
- **Iterací plánu:** 1 (plán schválen na první pokus) + 2 stop-and-describe momenty během exekuce
- **Uživatelských zpráv v session:** 4 (prompt + plán schválení + 2 re-approvaly po review autogenerated migrace)
- **Commity v session:** 9 (z plánovaných 7) — dva fix commity navíc po empirickém review

### Cíl

11 SQLAlchemy 2.0 async modelů ve třech logických skupinách
(auth / content / progress) podle kapitoly 4 BP, Alembic init s async
support, vygenerovat a aplikovat initial migraci, ověřit v psql.

### Co fungovalo na první pokus

- Plán s explicitními rozhodnutími (struktura modulu, enum strategy,
  updated_at strategy, CHECK constraints, sekundární indexy) prošel
  napoprvé bez korekce.
- `gen_random_uuid()` jako server_default v PG 16 — ověřeno před
  startem session že core ji poskytuje, žádné `pgcrypto` extension.
- Modely v 3 souborech (`auth.py`, `content.py`, `progress.py`) +
  base mixiny (`IDMixin`, `TimestampMixin`) — 80–200 řádek/soubor,
  1:1 mapuje brief.
- Alembic init s async template, env.py čte DATABASE_URL z app
  settings — funguje napoprvé.
- Autogenerate detekoval všech 11 tabulek, všechny FK s ondelete=
  'CASCADE', všechny composite UNIQUE, všechny custom indexy.
- `docker cp` workflow pro extrakci vygenerované migrace z containeru
  na host — bezproblémové.
- `alembic upgrade head` přes `docker compose exec backend` —
  bez chyby.

### Co bylo potřeba opravit

Po review prvního autogenerated výstupu vyšly najevo dva oddělené bugy
v Enum mappingu — oba obecně nezřejmé. Pythonista co dělá SA 2.0
poprvé do nich pravděpodobně narazí.

#### Bug 1: Enum NAMES místo VALUES v CHECK constraintu (commit 9693777)

`sa.Enum(MyStrEnum, native_enum=False, length=20)` vyrenderoval do
migrace uppercase enum NAMES (`'MULTIPLE_CHOICE'`, `'NUMERIC'`, …)
místo lowercase VALUES (`'multiple_choice'`, `'numeric'`, …).

```python
class ExerciseType(StrEnum):
    MULTIPLE_CHOICE = "multiple_choice"   # ← name vs value
```

Default SA Enum serializace používá `enum.name`, ne `enum.value`.
Pro StrEnum, kde `.value` je smysluplný řetězec, je to špatně:
`server_default=text("'locked'")` (lowercase) by selhal na CHECK
constraintu, který by očekával `'LOCKED'`.

**Fix:** přidat `values_callable=lambda obj: [e.value for e in obj]`
k oběma `Enum(...)` voláním. Druhá generace migrace správně rendruje
lowercase hodnoty.

**Lekce:** pro StrEnum (a jakýkoli Python enum, kde `.value` je
zamýšlený persistovaný řetězec) je `values_callable` povinný argument.

#### Bug 2: `create_constraint=False` jako default v SA 2.0 (commit d98b287)

Po prvním fixu migrace vypadala OK a byla aplikována. Empirický test
v psql ale odhalil druhý bug: **`INSERT … exercise_type = 'BOGUS'`
prošel** — žádný CHECK constraint na DB straně.

Příčina: V SQLAlchemy 2.0 změnili default `create_constraint` u
`sa.Enum` z `True` (1.x chování) na **`False`**. Bez explicitního
`create_constraint=True` typ generuje jen `VARCHAR(20)` a žádnou
kontrolu hodnot. `validate_strings=True` chytá výhradně Python-side
přiřazení přes ORM — raw SQL writes (psql, ručně psaná migrace,
stored procedures) projdou bez kontroly.

Past je zákeřná protože:

- Dokumentace SA Enum sama zmiňuje default změnu jen v changelog 2.0
  (snadno přehlédnutelné).
- Autogenerate nic ne-warnuje (model říká "varchar bez CHECK", schéma
  má varchar bez CHECK — alembic je v souladu).
- `\d` v psql prostě CHECK neukáže — pokud člověk nezkusí
  empirický test, projde to bez povšimnutí.

**Bezpečnostní dopad:** schéma bez CHECK je *typový komentář*, ne
bariéra. Při budoucích bulk operacích / backfill migracích / stored
procs žádná DB-side pojistka. Aplikační validace `validate_strings=
True` se uplatní jen pro ORM cestu.

**Fix:** přidat `create_constraint=True` k oběma `Enum(...)` voláním.
Po regenerate + apply má `\d exercises` mezi `Check constraints:`
jak `ck_exercises_difficulty_range`, tak `exercise_type` CHECK
na hodnotách. Empiricky ověřeno (uživatelem navržený jednorázový
test pokrývající oba bugy):

| INSERT exercise_type = | Výsledek | Co dokazuje |
|---|---|---|
| `'BOGUS'`           | ERROR violates check constraint | CHECK je aktivní (Bug 2 fix) |
| `'MULTIPLE_CHOICE'` | ERROR violates check constraint | hodnoty jsou lowercase (Bug 1 fix) |
| `'multiple_choice'` | INSERT 0 1 (success)            | správný formát projde |

**Lekce:** v SA 2.0 vždy explicitně `create_constraint=True` na
`Enum(native_enum=False, ...)`. Default-False je back-compat
trade-off, který obětuje bezpečnost schématu pro shorter migrations.
Při review autogenerated migrace nestačí pohled — empirický
boundary test je nutný.

### Rozhodnutí, která stojí za zaznamenání

- **Modules organized by domain group** (`auth.py`, `content.py`,
  `progress.py`) místo single-file nebo file-per-model. 80–200 řádek
  na soubor, 1:1 mapuje brief.
- **Enum jako Python `StrEnum` + SA Enum s `native_enum=False` +
  `create_constraint=True` + `values_callable`** — string + DB CHECK,
  žádné Postgres native enum (`ALTER TYPE ... DROP VALUE` v Postgresu
  neexistuje, takže přidávat / odebírat hodnoty je přívětivější přes
  CHECK).
- **`updated_at` přes `onupdate=func.now()`** — idiomatický SA 2.0
  pattern, nevyžaduje DB triggery. ORM-driven UPDATEs refrešují;
  raw SQL ne. Akceptovatelné, žádné raw SQL writes v MVP.
- **`gen_random_uuid()` v core PG 16** — žádný `CREATE EXTENSION
  pgcrypto`. Ověřeno před začátkem session.
- **Composite UNIQUE pokrývá leftmost FK index** — žádné redundantní
  `index=True` na FK sloupcích, které jsou leftmost v UNIQUE. Explicit
  indexy jen na FK sloupcích, které leftmost nejsou.
- **`cascade="all, delete-orphan", passive_deletes=True`** na ORM
  relationship; DB ON DELETE CASCADE dělá výmaz, ORM mu nestojí v
  cestě.
- **Clean-slate (downgrade + delete migration + regenerate) vs.
  additive migration** pro oba fixy: clean-slate zvolen, protože
  initial migrace rozdělená přes dva soubory je akademicky horší.

### Verifikační výstupy

`\dt`:
```
                List of relations
 Schema |         Name         | Type  |  Owner
--------+----------------------+-------+----------
 public | alembic_version      | table | mathingo
 public | courses              | table | mathingo
 public | daily_activities     | table | mathingo
 public | exercise_attempts    | table | mathingo
 public | exercises            | table | mathingo
 public | lesson_attempts      | table | mathingo
 public | lessons              | table | mathingo
 public | magic_link_tokens    | table | mathingo
 public | sections             | table | mathingo
 public | streaks              | table | mathingo
 public | user_lesson_progress | table | mathingo
 public | users                | table | mathingo
(12 rows)
```

`\d exercises` (selected):
```
exercise_type | character varying(20) | not null
difficulty    | integer               | not null | default 1
payload       | jsonb                 | not null | default '{}'::jsonb
Check constraints:
    "ck_exercises_difficulty_range" CHECK (difficulty >= 1 AND difficulty <= 5)
    "exercise_type" CHECK (exercise_type::text = ANY (ARRAY[
        'multiple_choice', 'numeric', 'true_false', 'matching', 'step_ordering'
    ]::text[]))
```

`alembic current`: `d35b3a02feb9 (head)`.

### Použité verze

| Komponenta | Verze |
|---|---|
| Alembic | 1.18.4 |
| SQLAlchemy | 2.0.x async (z uv.lock) |
| asyncpg | 0.30+ |
| Postgres | 16.13 |

### Dojem

- Plán s 7 explicitními rozhodnutími (sumarizovanými dopředu)
  zafungoval analogicky jako u session 003: schválení v jedné
  odpovědi, exekuce hned.
- Empirický test (`INSERT BOGUS / uppercase / lowercase`) jako
  součást verifikace je *právě ten* kus, který by se ve standardním
  flow přeskočil. Bez něho by Bug 2 projel a bezpečnostní dopad
  by se odhalil až za pár promptů (typicky v auth flow, který na
  status checks staví).
- SA 2.0 default `create_constraint=False` je past, kterou nezachytí
  ani lint ani autogenerate sám: model i DB jsou *v souladu*, jen oba
  bez CHECK. Empirický boundary test je jediná spolehlivá detekce.
- Two-fix narrative v gitu je pro thesis writeup hodnotnější než
  pseudo-bezchybná historie. Kapitola 6 dostává dva konkrétní příklady
  *vibe coding workflow* (model → autogenerate → empirical review →
  fix → re-generate → apply), oba se zachycenou stopou v commitech
  9693777 a d98b287.
- Granularita 9 commitů místo plánovaných 7 je v souladu s
  bibliografickým záznamem reálné práce: bumps mají hodnotu, ne
  jejich zametení.

---

## Session 005 — 2026-04-28 — Magic link autentizace (end-to-end)

- **Prompt ID:** #5
- **Iterací plánu:** 1 (plán schválen napoprvé s drobnými dodatky:
  `sonner` přidán, race condition explicitně dokumentovat, DoD deviace
  explicitně)
- **Uživatelských zpráv v session:** 3 (prompt + plán schválení + finální review)
- **Commity v session:** 12 plánovaných + 3 fix commity = **15**

### Cíl
End-to-end magic link auth flow: `/signin` → email z Resend → klik na
magic link → `/auth/verify` route handler → backend ověří + vystaví JWT
session cookie → onboarding (pro nové) nebo `/learn` (pro vracející se).
Žádné endpointy mimo auth doménu.

### Co fungovalo na první pokus
- Backend commits 1–7 (deps, config, seed migrace, email service, auth
  service, signin / verify / onboarding / me / signout endpointy)
  prošly bez kompilační chyby.
- Seed migrace pro 4MM101 kurz přes `ON CONFLICT (code) DO NOTHING` —
  idempotentní, jeden řádek vložen napoprvé.
- Resend API: signin endpoint vystavil row v `magic_link_tokens`,
  HTTP POST na Resend prošel, email reálně dorazil na inbox.
- shadcn init s `--defaults --yes`: bez interaktivních promptů, šest
  primitiv (button, input, label, card, radio-group, sonner) přidáno.
- E2E backend přes injected test token (vyhnutí se nutnosti čekat na
  email): verify → 302 + Set-Cookie ✓; consumed_at se nastavil; druhé
  použití stejného tokenu vrátilo `/signin?error=invalid_or_expired`;
  onboarding → 200; collision → 409; signout → cookie cleared;
  unauth /me → 401.

### Co bylo potřeba opravit

#### Bug 1: Compose nepřeposlal nové env vars do backend kontejneru (commit `c395dcf`)
Po commitu 1, kdy `app/config.py` získalo `resend_api_key`, `jwt_secret`,
`app_url` jako required fields, backend container po rebuildu spadl s
`pydantic_core.ValidationError: Field required`. `.env` na hostu měl
správné hodnoty, ale `docker-compose.yml` backend service má
**kuratorovaný `environment:` block** — nové vary musely být explicitně
přidány. Pydantic-settings nemůže splnit required field, který nikdy
nevidí.

**Fix:** doplnit `RESEND_API_KEY`, `JWT_SECRET`, `APP_URL` do
`environment:` v base `docker-compose.yml` (týká se i dev).

**Lekce:** Kuratorovaný env block je oboustranný — vidí jen to, co se
vyjmenuje. Při přidání config keys nezapomenout na compose passthrough.
Plus: u required Pydantic fields se chyba projeví jako container crash
loop, ne jako varování.

#### Bug 2: shadcn Button nemá `asChild` prop (commit `7b077ac`)
Frontend build selhal v TypeScript fázi:
`Property 'asChild' does not exist on type ... ButtonProps`. shadcn
"new-york" registry teď generuje Button postavený nad `@base-ui/react`
(ne Radix). Base UI Button neexponuje `asChild`. Můj
`<Button asChild><Link>...</Link></Button>` (Radix-style pattern)
nefungoval.

**Fix:** stylovat Link přímo přes `buttonVariants` helper exportovaný
z `button.tsx`:
```tsx
<Link className={cn(buttonVariants({size:"lg"}), "mt-8")}>Začít</Link>
```
Sémanticky lepší — je to navigation link, ne button.

**Lekce:** shadcn API se mění napříč registry style verzemi a
underlying primitive libs. Při použití komponent z čerstvě init-ovaného
projektu ověřit aktuální export shape (`Read` na vygenerovaný soubor),
nepředpokládat staré Radix pattern z paměti.

#### Bug 3: Verify route handler vracel redirect na 0.0.0.0 (commit `309a84b`)
Smoke test ukázal:
`/auth/verify (no token) → 302 → https://0.0.0.0:3000/signin?error=...`.
Next.js `req.url` v route handleru vrací **interní listen address**, ne
externí host (i když nginx forwarduje `Host` header). `new URL(location,
req.url)` tedy konstruoval špatnou base.

**Fix:** nepoužívat `NextResponse.redirect` (chce absolutní URL). Místo
toho ručně skládat `NextResponse(null, {status:302, headers:{Location:
relative_path}})`. Browser per RFC 7231 resolvuje relative Location
proti URL skutečně odeslanému, takže původní `mathingo.cz` se použije.

**Lekce:** Za reverse proxy se automaticky nepřebírá `Host` header do
parsed origin. Pro redirect z route handleru je `Location: <relative
path>` nejbezpečnější (browser to vyřeší, ne server).

### Rozhodnutí, která stojí za zaznamenání

- **Token bezpečnost:** `secrets.token_urlsafe(32)` (32 bytes URL-safe) →
  SHA-256 hex digest v DB. Plain token jen v emailu, nikdy nepersistován.
- **JWT cookie:** HS256, 30-day expiry, `mathingo_session` cookie
  HttpOnly + Secure (jen v prod) + SameSite=Lax + Max-Age. Žádný
  refresh token (out of MVP scope).
- **CSRF:** SameSite=Lax + CORS limit na `https://mathingo.cz` +
  POST-only mutace = adekvátní bez explicit CSRF tokenu.
- **Email enumeration:** `/signin` VŽDY vrací `{"status":"sent"}`,
  žádný early return na neexistujícího uživatele. DB write a Resend
  volání běží stejně v obou případech (uživatel vzniká až ve `/verify`)
  → žádný timing oracle.
- **Inline HTML email** (ne Jinja). Při druhé šabloně refactor na
  Jinja v jednom commitu.
- **Next.js route handler pro `/auth/verify`** (ne nginx rewrite).
  Backend zůstává čistá API pod `/api/*`, frontend vlastní user-facing
  URL prostor.
- **Display name uniqueness app-vrstva, case-sensitive.** SELECT-then-
  INSERT race tolerated pro MVP, dokumentováno níže.
- **Seed migrace přes `ON CONFLICT (code) DO NOTHING`** + lookup by
  code ve verify endpointu. Žádné UUID hardcodované v Python kódu.
- **Sonner pro toast feedback** — display_name collision teď + budoucí
  XP earned / streak prolonged notifikace.

### Known limitations (acceptable for MVP)

- **display_name uniqueness race condition.** SELECT-then-INSERT
  pattern v `POST /auth/onboarding` má TOCTOU race: dva concurrent
  submity stejného display_name můžou oba projít. Akceptabilní pro
  MVP s low concurrent signup. Fix v budoucnu = normalized lower-case
  sloupec s DB UNIQUE indexem (jednou migrací přidat
  `display_name_normalized`, naplnit `LOWER(display_name)`, UNIQUE
  index, app vrstva validuje proti normalizované formě).
- **Magic link cleanup.** Žádný background job nemaže expired /
  consumed tokeny. `magic_link_tokens` časem narůstá. Cleanup task
  v samostatné session (cron uvnitř backendu nebo periodická migrace
  `DELETE WHERE expires_at < now() - interval '7 days'`).

### Known deviations from CLAUDE.md DoD

- **Tests deferred to a follow-up session.** CLAUDE.md DoD vyžaduje
  "covered by at least one automated test (unit or integration)".
  Tato session končí bez pytest tests pro auth flow. Důvod: 12+ commit
  session, testovací infrastruktura (httpx mock pro Resend, async test
  DB, fixtures) by sessionu prodloužila o ~5 commitů. Plán pokrytí v
  samostatném *prompt #5.1 — auth tests*: pytest-asyncio, respx (httpx
  mock), tmp test schema přes alembic na samostatné test DB. Tato
  deviace je vědomá, ne přehlédnutí.

### Použité verze (přírůstky)

| Komponenta | Verze |
|---|---|
| pyjwt | 2.12.1 |
| email-validator | 2.3.0 |
| dnspython (transitivní) | 2.8.0 |
| shadcn registry style | "new-york" + Base UI primitives |
| @base-ui/react | 1.4.x |
| sonner | 2.0.7 |
| lucide-react | 1.12.0 |

### Verifikační výstupy

**Backend e2e přes vstříknutý test token:**

```
POST /api/auth/signin                            → 200 {"status":"sent"} + token row
GET  /api/auth/verify?token=<plain>              → 302 → /onboarding + Set-Cookie
GET  /api/auth/me   (s cookie)                   → 200 {id, email, display_name:"", daily_xp_goal:20}
GET  /api/auth/verify?token=<same plain>         → 302 → /signin?error=invalid_or_expired
POST /api/auth/onboarding {display_name, goal}   → 200 {"status":"ok"}
GET  /api/auth/me                                → 200 (updated)
POST /api/auth/onboarding (kolize z 2. uživatele)→ 409 {"detail":"display_name_taken"}
POST /api/auth/signout                           → 200 + Set-Cookie clearing
GET  /api/auth/me   (bez cookie)                 → 401
```

**Frontend smoke (HTTP status):**

```
/             → 200
/signin       → 200
/check-email  → 200
/onboarding   → 307 → /signin (anonymní)
/learn        → 307 → /signin (anonymní)
/auth/verify  → 302 → /signin?error=invalid_or_expired (bez tokenu)
```

**Resend integrace:** signin endpoint úspěšně volal Resend API,
`magic_link_tokens` row vytvořen, email reálně doručený do inboxu na
`filip.cupl@gmail.com`. Manuální klik na link v reálné GUI session +
end-to-end frontend flow — ověřuje uživatel ve své prohlížečce.

### Dojem

- 12 plánovaných commitů + 3 fix commity = 15. Tři fixy během
  jedné session je víc než předchozí sessiony — odpovídá to faktu,
  že auth flow integruje mezi více vrstvami (config / DB / docker-
  compose / nginx / frontend / Next.js), kde každá má vlastní
  subtleties.
- Bug 1 (compose env passthrough) by mě možná napadl až ze zkušenosti.
  V budoucnu si pamatovat: jakákoli nová required `Settings` field
  musí být passthroughovaná v compose `environment:` bloku.
- Bug 2 (shadcn API drift): shadcn ekosystem se vyvíjí rychleji než
  paměť. Při použití komponent z čerstvě init-ovaného projektu
  ověřovat reálný export shape čtením generated souboru.
- Bug 3 (route handler URL parsing): Next.js za reverse proxy má
  subtle gotcha kolem origin parsování. Relative Location je
  nejjednodušší robustní fix; řeší to navíc i případnou budoucí změnu
  hostu.
- *Tests deferred* je vědomé — auth bez tests do produkce není ideál,
  ale explicitní DoD deviation v journalu je transparentnější než
  falešný claim "all tests passing".
- Resend integrace prošla bez bumps — DNS verifikace domény + API
  klíč v `.env` stačily. Moment, kdy email reálně dorazí, je něco,
  co testovací mock nezprostředkuje.

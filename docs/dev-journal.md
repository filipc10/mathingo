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

---

## Session 006 — 2026-04-29 — Design system rollout

- **Prompt ID:** #6
- **Iterací plánu:** 1 (plán schválen napoprvé s drobnými dodatky:
  whitespace na landingu, menší čísla na PathStone, visual check
  kromě curl smoke)
- **Uživatelských zpráv v session:** 3 (prompt + plán schválení + finální review)
- **Commity v session:** 7 plánovaných + 1 fix commit = **8**

### Cíl
Z defaultního Tailwind/shadcn templatu udělat konzistentní Duolingo-
inspired design system: Nunito font, primary modrá `#0073FF`, akcent
zelená `#22C55E`, 14 px border radius, polish všech 5 existujících
obrazovek. Žádné funkční změny, žádný backend touch, žádný dark mode.

### Co fungovalo na první pokus
- Replace `globals.css` připraveným obsahem + drobná adaptace
  `@plugin "tailwindcss-animate"` → `@import "tw-animate-css"`
  (už nainstalovaný shadcn v sesssion 005). Žádný nový dep.
- Replace fontů v `layout.tsx`: Geist/Geist_Mono → Nunito s vahami
  400/600/700/800/900 přes `next/font/google`. `latin-ext` subset
  pokrývá českou diakritiku.
- shadcn primitivy (button, input, card) — manuální edit base
  class strings (font-bold, h-11, shadow-sm), ne `npx shadcn add`
  (které by přepsalo prompt-#5 fixy).
- Card-style XP radio v onboardingu přes Tailwind `has-[[data-checked]]:`
  selector — bez React state, čistě CSS, label wrapping
  RadioGroupItem.
- PathStone komponent + 7 kamenů s offsety `[0, +56, +80, +56, 0,
  -56, -80]` — sinusoidální vlna, layout flexbox column +
  `transform: translateX(...)` per stone.
- next/font/google self-hosting Nunito woff2 (preloaded) + body
  class `nunito_*-module__*__variable` ze stránek HTML inspect.
- Favicon `app/icon.svg` (32×32 SVG) + OG image `app/opengraph-
  image.tsx` přes built-in `next/og` `ImageResponse` — žádný nový
  dep, vše Next 15 conventions.

### Co bylo potřeba opravit

#### Bug: OG image URL zaháknuté na `localhost:3000` (commit `4f356c6`)

Po commitu 7 měl rendered HTML `og:image` URL ve formě
`http://localhost:3000/opengraph-image?...`. Crawler (Twitter, Slack
preview) by stáhl localhost a selhal.

**Příčina:** Next 15 počítá absolutní OG URL podle `metadataBase`
v root metadata. Když není nastavený, defaultuje na request URL —
ale při statické pre-rendering build fázi je „request URL" interní
listen address (`http://localhost:3000`).

**Fix:** v `layout.tsx`:
```tsx
metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL ?? "https://mathingo.cz"),
```

Po fixu HTML correctly emits
`<meta property="og:image" content="https://mathingo.cz/opengraph-image?..."/>`.

**Lekce:** každá nová stránka s metadata, která produkuje absolutní
URL (OG image, canonical link, sitemap), potřebuje `metadataBase`
v root. Buďto hardcoded, nebo z env. Default behavior Next.js to
neflagne errorem — jen tiše použije localhost.

### Rozhodnutí, která stojí za zaznamenání

- **`tw-animate-css` místo `tailwindcss-animate`** — provided
  globals.css měl `@plugin "tailwindcss-animate"`, ale shadcn 4.x
  nainstaloval `tw-animate-css` (jiný balíček, stejné utility
  classes). Adaptoval jsem o jeden řádek na `@import "tw-animate-
  css"`. Žádný nový dep, žádné side-effecty (`animate-in`, `fade-in`,
  `slide-in-*` jsou identické).
- **Nunito** (Google Fonts free, Duolingo-like rounded geometric)
  s vahami 400/600/700/800/900 přes `next/font/google`. Self-hosting
  + `display: "swap"` (text se vyrendruje s fallback fontem ihned,
  Nunito doplní jakmile dorazí). `latin-ext` subset pro českou
  diakritiku — bez něj by `Mathingo` rendrovalo, ale `přihlas`
  by visel na fallback glyphs.
- **oklch color space** — moderní, perceptually uniform; primary
  `oklch(0.59 0.22 252)` ≈ `#0073FF`. Tailwind 4 podporuje
  natively, browsers (Chrome 111+, Safari 15.4+, Firefox 113+)
  taky.
- **Card-style radio** přes `has-[[data-checked]]:` Tailwind
  selector místo klasického malého radio circle. Lepší UX
  (větší klikatelná plocha, jasná visual selection), bez extra
  React state — celá selection logika je v CSS přes Base UI's
  `data-checked` attribute. Pure CSS přístup je robustní (žádný
  re-render, žádný controlled-component plumbing).
- **CardTitle stays `<div>`** v shadcn primitivu, sémantická
  heading hierarchie patří per-instance do consumer kódu (per
  user decision z plánu). Globální `h1-h4` styly v `@layer base`
  se aplikují na semantic h-tags v page komponentách.
- **No framer-motion** — Tailwind `animate-in fade-in slide-in-
  from-bottom-2 duration-500` na landing hero + `transition-
  transform hover:scale-110` na PathStone + Loader2 spinning
  icon. Stačí pro MVP polish, žádný nový dep.
- **PathStone `cursor-not-allowed` + `disabled`** na locked
  state — visually i sémanticky nezklikatelné. Available state
  klikatelný ale nikam nevede (pro tuto session jen vizuální
  prototyp; navigace přijde s implementací cvičení).
- **Top bar v `/learn` inline (ne extrakce)** — jediný consumer.
  Refactor až s druhým use case (např. profile page v dalším
  promptu).

### Out of scope této session
- **Dark mode** — vědomě vynechán. Zdvojil by visual QA práci a
  thesis komise to nevyžaduje. Tokens v `globals.css` jsou jen
  light; `.dark` selector dropnut.
- **Reálná data v top baru** — streak `🔥 0 dní` a XP `0 / N XP`
  jsou hardcoded placeholders. Backend endpointy pro streak/XP
  ještě neexistují, refactor top baru na komponentu se stane,
  až přijdou (next session).
- **Reálná navigace v `/learn` path** — kameny jsou jen vizuální
  prototypy; available stone klikne, ale nikam nenaviguje. Lesson
  runtime + routing v dalším promptu.
- **Tests** — pokračuje DoD deviation z prompt #5 (auth tests
  deferred). Visual diff testy (Chromatic / Percy) by byly pro
  thesis overkill.

### Použité verze (přírůstky)

| Komponenta | Verze |
|---|---|
| Nunito (Google Fonts) | weights 400/600/700/800/900, latin + latin-ext |
| Tailwind CSS | 4.x (z prompt #2) |
| tw-animate-css | 1.4.0 (z prompt #5) |
| oklch color space | natively v Tailwind 4 |

### Verifikační výstupy

**Smoke (HTTP status):**
```
/                         → 200
/signin                   → 200
/check-email              → 200
/onboarding (anon)        → 307 → /signin
/learn (anon)             → 307 → /signin
/auth/verify (no token)   → 302 → /signin?error=invalid_or_expired
/icon.svg                 → 200
/opengraph-image          → 200 (PNG)
POST /api/auth/signin     → 200 (auth flow nedoznal regrese)
```

**Inspekce HTML root stránky:**
- `<html lang="cs" className="nunito_…__variable">` — Nunito CSS
  variable applied ✓
- `<link rel="preload" .../>` na woff2 fontů ✓
- `<meta property="og:image" content="https://mathingo.cz/
  opengraph-image?…">` — absolute URL ✓
- `<link rel="icon" href="/icon.svg?…" type="image/svg+xml">` ✓
- Button rendering: `bg-primary text-primary-foreground … h-11
  gap-2 px-8 text-lg font-bold rounded-lg` ✓ (new design tokens
  applied)

**Visual check** (prováděn manuálně mimo Claude Code session — GUI
prohlížeč není v exekuční prostředí dostupný):
- Provedeno nahrubo přes HTML/CSS inspect: žádný overflow, žádné
  missing tokens, žádný z bývalých Geist font referencí v nové
  HTML.
- Screenshot mobile + desktop viewportů + visual review obou je
  na uživateli (nemožné z této session).

### Dojem

- 7 plánovaných commitů + 1 fix = 8. Pouze jeden bump (metadataBase),
  což je nejméně bumpů v session od scaffold. Design polish je
  méně cross-vrstvový než auth flow — typografie / barvy /
  layout všechno hraje na jedné vrstvě (frontend Tailwind + JSX),
  takže méně integration gotchas.
- Adaptace `@plugin tailwindcss-animate` → `@import tw-animate-
  css` je *přesně* ten typ rozhodnutí, kde provided CSS od
  uživatele obsahuje hint na nový balíček, ale aktuální projekt
  má alternativu. Místo slepého paste je lepší adaptovat.
- `has-[[data-checked]]:` Tailwind selector pro card-style radio
  je elegantní — pure CSS, žádný React state plumbing.
  Standardní React tutorial by ti řekl "use useState + onChange",
  ale Base UI emits `data-checked` jako side effect, takže CSS
  to pickne free.
- `metadataBase` bug: `next/og` ImageResponse je hezký, ale
  bez explicitního `metadataBase` se OG URL stane localhost. Až
  bude site shared on Twitter/Slack v 1-2 dnech, je dobré, že
  to bylo zachyceno před launchem.
- Pro thesis writeup: design polish session je dobrý kontrast
  vůči auth/db sessionám — vizuální / typografická rozhodnutí
  vedle technical/security. Kapitola 6 (vibe coding workflow)
  získá pohled, jak se Claude Code chová s "fluffy" task: méně
  konkrétních specifikací, více estetických rozhodnutí, ale
  stejná struktura plán → execution → review.

---

## Session 007 — 2026-04-29 — Dark mode + first_name + vokativ

- **Prompt ID:** #7
- **Iterací plánu:** 1 (plán schválen napoprvé s úpravami: czech-vocative
  knihovna místo hand-rolled heuristic, prefill display_name z existing
  user record, plus user dropoval logo + favicon do repa pro integraci)
- **Uživatelských zpráv v session:** 3 (prompt + plán schválení +
  „favicon je šíleně malý" feedback)
- **Commity v session:** 9 plánovaných + 2 fix commity (favicon size,
  v dvou iteracích) = **11**

### Cíl

Tři logicky propojené změny:
1. Dark mode jako default napříč aplikací (žádný toggle).
2. Rozdělit `display_name` na `first_name` (oslovení, NOT unique) +
   `display_name` (handle, unique).
3. České vokativní oslovení — `vocative("Filip") → "Filipe"`.

### Co fungovalo na první pokus

- Replace `globals.css` připraveným dark obsahem + `dark` className
  na `<html>`. Všechny existující komponenty (z prompt #5, #6)
  auto-pickly tokens — žádné explicit dark-mode override potřebné.
- Alembic autogenerate detekoval nový `first_name` sloupec na první
  pokus (po model edit + container rebuild).
- E2E reonboarding flow ověřen přes injected token: nový user
  s `first_name=""` → /onboarding ✓; po onboarding submit →
  display_name a first_name updatnuté v DB ✓; pokus o submit
  s prázdným first_name → 422 s Pydantic detail ✓.
- `czech-vocative@2.1.0` knihovna pokrývá víc než moje původní
  hand-rolled heuristic by zvládla — viz „Test cases" níže.
- Logo `<Image>` v /learn top baru přes next/image — automatická
  AVIF/WebP optimalizace na produkci.

### Co bylo potřeba opravit

#### Bug: favicon vypadal šíleně malý (commits `b4ce907`, `c8f1878`)

První integrace favicon source PNG (1536×1024) → resize na 512×512
proběhla přes pad-to-square (transparent okraje top/bottom). Po
resize byl skutečný non-transparent obsah jen `bbox 191×188`
uvnitř `512² canvasu` — fill ratio 37 % × 37 %. Při browser render
na 16 px nebo 32 px favicon „M" byl drobný uprostřed velké prázdné
plochy.

Uživatel feedback (1. kolo): „Favicon je šíleně malý."

**Fix v1 (`b4ce907`):** re-crop existujícího `icon.png` k jeho
reálnému content bbox + 8 % margin, pad na čtverec, resize zpět na
512×512. Nový bbox 441×434 = fill ratio 86 % × 85 %. Plus přidán
`apple-icon.png` 180×180 pro retina iPhone home-screen tiles.

Uživatel feedback (2. kolo): „ještě by ta ikona mohla být větší".

**Fix v2 (`c8f1878`):** snížit margin z 8 % na 2 %. Fill ratio
~96 % × 93 % — content prakticky zaplňuje canvas. Edge-to-edge
look typický pro square brand-mark icons (Twitter X, GitHub
Octocat). Apple-icon regenerován z téhož canvasu.

**Lekce:** Pro favicon nestačí jen square dimension — content
musí zaplnit většinu canvasu (>90 %). Pad-to-square preserve aspect
funguje pro hero images, ale pro tiny render na 16 px je jakákoli
viditelná prázdná oblast moc drahá v perceived brightness ratio.
8 % bylo „bezpečné" víc než „dostatečné". Iterace s reálným uživatelským
viewem byly nutné — Claude Code nemá náhled do skutečného browser
renderu.

### Rozhodnutí, která stojí za zaznamenání

- **Dark mode jako default, žádný toggle** — komise vidí Mathingo
  v dark, žádný light/dark preference matching s prefers-color-scheme.
  `.light` selektor zachován v CSS jako parked block, kdyby se to
  v budoucnu chtělo přepnout. Akademický framework v thesis
  kapitole 6: srovnání s Duolingo dark mode + odlišení od typických
  „bílých" edukačních apps.
- **`first_name` separátně od `display_name`** — UX motivace: jméno
  je oslovení (osobní), přezdívka je handle (veřejná v žebříčku).
  Spojení do jediného sloupce v session 004 byla zjednodušující
  zkratka. Po této session má každé pole vlastní constraints
  (first_name 1-40 not unique, display_name 3-30 unique).
- **Empty string sentinel pro „needs onboarding"** zachováno + 
  rozšířeno: `first_name=="" or display_name==""` triggers
  `/onboarding`. Žádný nový boolean flag column. Existující user
  (Filip) získal `first_name=""` přes server_default v migraci a
  bude reonboardován, kdy se znovu signinne.
- **Migration server_default + alter_column drop** — `add_column
  ... server_default=''` backfill existing rows; pak
  `alter_column server_default=None` čistí default tak, aby budoucí
  inserts musely explicit. Cleaner schema, žádný persistent default
  v DB.
- **`czech-vocative` knihovna místo hand-rolled rules** — uživatel
  override po prvním plánu. Knihovna pokrývá irregulární vokativy
  (Pavel → Pavle, Karel → Karle), které heuristika z briefu by
  netrefila. Přidaná závislost vědomě schválená v plánu (per
  CLAUDE.md hard-constraint #1).
- **Onboarding form prefill `display_name` z existing user, ale
  `first_name` empty** — pro reonboarding existujících uživatelů
  (Filip má `display_name="Filip"` survivuje migraci) lepší UX:
  nemusí psát handle znovu, jen vyplní jméno. Pro nového uživatele
  oba inputy prázdné.
- **Logo přes `next/image` v /learn top baru** — z 1672×941 source
  resized na 1200×675 a uložen v `frontend/public/logo.png`.
  Next image pipeline pak generuje AVIF/WebP variants na
  produkční doméně.

### Test cases pro vokativ

```
vocative("Filip")   → "Filipe"   ✓
vocative("Pavel")   → "Pavle"    ✓ (irregular — drops -e- before -l)
vocative("Karel")   → "Karle"    ✓ (irregular)
vocative("Michal")  → "Michale"  ✓
vocative("Tomáš")   → "Tomáši"   ✓
vocative("Petr")    → "Petře"    ✓
vocative("Anna")    → "Anno"     ✓
vocative("Marie")   → "Marie"    ✓ (ženské -e/-ě beze změny)
vocative("Honza")   → "Honzo"    ✓
vocative("Jiří")    → "Jiří"     ✓
vocative("Mateusz") → "Mateuszi" ✓ (cizí jméno, knihovna stále
                                   produkuje vokativní formu)
vocative("Eva")     → "Evo"      ✓
vocative("Lucie")   → "Lucie"    ✓
vocative("Aleš")    → "Aleši"    ✓
```

Všechny standardní česká jména korektně. Cizí (Mateusz) dostávají
„best-effort" inflekci — knihovna Czech-rules-applies-to-foreign-input.
Pro thesis kapitolu 4 (UX i18n): full Czech inflection coverage je
detail, který hand-rolled approach by neuznesl bez signifikantního
rozšíření.

### Použité verze (přírůstky)

| Komponenta | Verze |
|---|---|
| czech-vocative | 2.1.0 |
| Pillow (host-only, image processing) | 10.2.0 |
| Alembic migration | `5d9486ef38a3` (add first_name to users) |

### Verifikační výstupy

**HTTP smoke:**
```
/                       → 200
/signin                 → 200
/check-email            → 200
/onboarding (anon)      → 307 → /signin
/learn (anon)           → 307 → /signin
/icon.png               → 200 (image/png, ~96%×93% content fill po druhém fixu)
/apple-icon.png         → 200 (180×180)
/logo.png               → 200 (1200×675 served via next/image pipeline)
```

**E2E auth flow (přes injected token):**
```
POST /api/auth/signin → 200
GET  /api/auth/verify (s tokenem) → 302 → /onboarding + Set-Cookie
GET  /api/auth/me → 200 {first_name: "", display_name: "", goal: 20}
POST /api/auth/onboarding {first_name:"Pavel",...} → 200 {"status":"ok"}
GET  /api/auth/me → 200 {first_name: "Pavel", display_name: "pavel-e2e", ...}
GET  /learn (s cookie) → 200, HTML obsahuje "Vítej, Pavle!" (vokativ aktivní)
POST /api/auth/onboarding {first_name:"",...} → 422 (Pydantic min_length=1)
```

**HTML rendering (s cookie pro /learn):**
- `<html lang="cs" class="dark nunito_…__variable">` ✓
- `<link rel="icon" href="/icon.png?icon.5a7e624b.png" sizes="512x512">` ✓
- `<link rel="apple-touch-icon" href="/apple-icon.png?…" sizes="180x180">` ✓
- `<img src="/_next/image?url=%2Flogo.png&…">` (next/image optimized) ✓

**DB schema after migration:**
```
users.first_name | character varying(40) | NOT NULL | (no default)
users.display_name | character varying(40) | NOT NULL | (no default)
```

### Known limitations / out-of-scope

- **DB constraint `display_name` zůstává `VARCHAR(40)`** zatímco
  app vrstva validuje 3-30. Schema-level zúžení na `VARCHAR(30)`
  by potřebovalo destruktivní `ALTER TYPE` — pro 1 existing user
  s `display_name="Filip"` (5 chars) zbytečné. Lze přidat constraint-
  -level migraci později pokud bude potřeba.
- **Vocative pro nominativ-only (např. "Anna" stays "Anno")** —
  není rozlišení mezi mužem/ženou, knihovna detekuje přes endings.
  Pro hraniční případy (epicene names) může produkovat unexpected
  formy, ale v Czech jméneckém prostoru neobvyklé.
- **Existující user `display_name="Filip"` se survives migraci.**
  Po jeho příštím signinu zde se musí znovu projít onboardingem
  (kvůli prázdnému first_name). UX detail: form předvyplní
  display_name, ale ne first_name.

### Dojem

- 9 plánovaných + 2 fixy = 11 commitů. Vizuální bug (favicon size)
  vyžadoval dvě iterace — moje první oprava na 86 % fill byla pro
  uživatelův vkus stále moc malá. Druhá iterace na ~96 % fill prošla.
  Není to typ chyby, kterou by HTTP smoke nebo Pydantic
  validation chytila — vyžaduje skutečné prohlížení malého
  rendered icon. Ukazuje, že reálný visual feedback od uživatele je
  jediný spolehlivý gate pro tento typ rozhodnutí.
- `czech-vocative` knihovna je pěkný pattern „specialized
  third-party" rozhodnutí: hand-rolled regex would cover 60 %
  cases, knihovna ~100 %, cena = jeden npm dep. Pro thesis
  kapitolu 6 to je good case study o tom, kdy „postavit vlastní"
  vs. „použít existující" trade-off.
- Migration s `server_default + alter_column drop` je standardní
  Alembic pattern pro NOT NULL backfill, který autogenerate
  nezvládne. Manuálně doplněno.
- Existing user reonboarding přes empty-string sentinel zacházel
  čistě bez nového boolean flag column. Ten přístup škáluje
  i pro budoucí onboarding fields (např. preferred language,
  notification preferences) — všechno přes sentinel hodnoty,
  routovací gate v jednom místě.
- Pro thesis writeup: kombinace „logically related" změn v jedné
  session je interesting — ukazuje, jak Claude Code zvládá
  multi-track plánování (DB + backend + frontend + i18n) bez
  ztráty kontextu mezi vrstvami.

---

## Session 008 — 2026-04-29 — Seed obsah + read-only content API

- **Prompt ID:** #8
- **Iterací plánu:** 1 (plán schválen napoprvé s drobnými dodatky:
  empirický check JSON escapu, sloučit commit 3+4 do jednoho)
- **Uživatelských zpráv v session:** 2 (prompt + plán schválení)
- **Commity v session:** 4 (z plánovaných 5 — empty marker commit
  vynechán dle session-004 patternu)

### Cíl

Naplnit DB ukázkovým vzdělávacím obsahem (1 sekce „Limity funkce",
4 lekce, 10 cvičení) v kurzu 4MM101 přes Alembic seed migraci.
Vystavit obsah přes 3 read-only GET endpointy (`/courses/<id|code>`,
`/courses/<id|code>/structure`, `/lessons/<uuid>`). Žádné UI změny.

### Co fungovalo na první pokus

- Plán schválen napoprvé. 6 explicitních rozhodnutí (migration
  approach, idempotence, struktura souborů, resolver, KaTeX
  escaping, žádný auth) bylo dostatečně pre-validováno, takže
  uživatel přidal jen zpřesnění (empirický check + commit merge).
- Pydantic schemas: 6 modelů (CourseResponse, LessonSummary,
  SectionWithLessons, CourseStructure, ExerciseResponse,
  LessonDetail) s `from_attributes=True` — endpoint handlery
  hand-off ORM rows přímo do `model_validate` bez explicit
  conversion.
- API router se 3 endpointy + `_load_course` resolver (UUID-or-
  code) — funguje na první build. UUID parsing přes `try: UUID(s)`
  + fallback na `code` lookup.
- `selectinload` eager loading: `selectinload(Course.sections)
  .selectinload(Section.lessons)` pro structure, `selectinload(
  Lesson.exercises)` pro lesson detail. Žádné N+1, ordering
  zajištěno přes `order_by="<sibling>.order_index"` na
  relationship z session 004.
- Empirický KaTeX escape check pochází z plánu uživatele:
  ```
  curl /api/lessons/<id> | jq '.exercises[0].prompt'
  → "Co intuitivně znamená zápis $\\lim_{x \\to 2} f(x) = 5$?"
  ```
  Backslashy double v JSON (correct), single v `python -c repr` po
  parsování (correct), single v DB stored (correct). Žádné
  double-escape kolize.

### Co bylo potřeba opravit

#### Drobnost: první Write na migrate file selhal (Read-first guard)

Po `alembic revision -m "..."` vznikl skeleton migrace v containeru.
`docker cp` ho přenesl na host. Když jsem ho chtěl přepsat reálným
obsahem, Write tool odmítl s „File has not been read yet" — guard,
který chrání před overwrite bez prior Read. Standardní pattern
Claude Code's editing flow.

**Fix:** Read si soubor jednou + Write přes existing path. Mezitím
prázdný `upgrade()` skeleton se aplikoval na DB přes `alembic
upgrade head` (no-op, žádné insert). Přes `alembic downgrade -1`
revertnul + Write s reálným obsahem + apply znovu. Žádný side
effect na DB.

**Lekce:** `alembic revision -m` generuje skeleton soubor — než
se ho přepíše, vždycky ho jednou Read. Ověřit `alembic current`
po každém upgrade/downgrade je laciné a chytá tichý no-op.

### Rozhodnutí, která stojí za zaznamenání

- **Inline `sa.table()` Core SQL místo ORM Session v migraci.**
  Decoupled od ORM modelů — pokud v budoucnu Exercise model změní
  schema, historická migrace zůstane platná. Plus parametrized
  binds řeší LaTeX escaping a JSONB serializaci automaticky bez
  manuálního `json.dumps()`.
- **Idempotence přes `ON CONFLICT (composite) DO NOTHING`** na
  composite UNIQUE z session 004. `_upsert_returning_id` helper
  handles both paths: insert returning new id, fallback select
  when row existed. Re-běh migrace = no-op. Robustní pro reálná
  deployment scenarios kdyby někdo `alembic upgrade head` spustil
  vícekrát.
- **`services/content.py` neexistuje** — `_load_course` privátní
  fn v `api/content.py`. Premature abstraction antipattern; když
  přibude druhý use case, extract.
- **Žádný auth na content endpointech.** Vědomě veřejné.
  Read-only curriculum content nemá privacy sensitivity. Komise
  může v Swagger procházet bez login. Auth-gating = friction
  bez bezpečnostního benefitu. Pokud změna potřeba, je to jeden
  `Depends(get_current_user)` v každém handleru.
- **KaTeX backslash flow (Python literal → DB → JSON response →
  browser → KaTeX):** Python `"\\lim..."` = string `\lim...` →
  DB ukládá `\lim...` (single) → JSON encoder vyplive
  `"\\lim..."` (double in JSON syntax) → browser `JSON.parse`
  dekoduje na `\lim...` → KaTeX renderuje. Bind parametry
  v migraci řeší celý round trip bez ručního escaping.
- **Sloučit commit 3+4** (seed + apply) do jednoho commitu místo
  empty marker. Konzistentní s session 004 patternem; verifikační
  evidence v commit body.

### Použité verze a artefakty

| Komponenta | Verze / Identifikace |
|---|---|
| Alembic migration | `f4ed5e40904a` (seed 4MM101 limity section content) |
| Sekce | 1 — „Limity funkce" |
| Lekce | 4 — Pojem limity, Limity v nevlastních bodech, Jednostranné limity, Pravidla pro výpočet limit |
| Cvičení | 10 — 6× multiple_choice + 4× numeric |

### Verifikační výstupy

**Seed po apply:**
```
    section    |           lesson            | xp_reward | exercise_count
---------------+-----------------------------+-----------+----------------
 Limity funkce | Pojem limity                |        10 |              3
 Limity funkce | Limity v nevlastních bodech |        15 |              2
 Limity funkce | Jednostranné limity         |        15 |              2
 Limity funkce | Pravidla pro výpočet limit  |        20 |              3
```

**API endpointy:**
```
GET /api/courses/4MM101                          → 200 (CourseResponse)
GET /api/courses/<uuid>                          → 200 (CourseResponse)
GET /api/courses/4MM101/structure                → 200 (4 lessons in order)
GET /api/lessons/<lesson1-uuid>                  → 200 (3 exercises in order)
GET /api/courses/UNKNOWN                         → 404 (course_not_found)
GET /api/lessons/00000000-0000-0000-0000-…       → 404 (lesson_not_found)
GET /api/lessons/not-a-uuid                      → 422 (Pydantic UUID validation)
```

**KaTeX escape (per uživatelův návrh):**
```
DB stored:    "Co intuitivně znamená zápis $\lim_{x \to 2} f(x) = 5$?"
JSON output:  "Co intuitivně znamená zápis $\\lim_{x \\to 2} f(x) = 5$?"
Python repr:  'Co intuitivně znamená zápis $\\lim_{x \\to 2} f(x) = 5$?'
              (\\ in repr = single \ in actual string)
```

Žádný double-double escape (`\\\\`) v JSON — round trip čistý.

### Known limitations / out-of-scope

- **Pouze 2 typy cvičení** — multiple_choice + numeric. Brief
  explicit. true_false, matching, step_ordering jsou v enumu
  z session 004, ale obsah pro ně přijde s rozšířením kurikula.
- **Žádný UI rendering cvičení.** `/learn` zůstává placeholder
  s 7 stones. Lesson runner UI + napojení na content API přijde
  v promptu #9.
- **Žádné progress tracking** v této session — progress, streak,
  XP earning přijdou s lesson runtime.
- **Tests odložené** — pokračování DoD deviation z session 005.

### Dojem

- Plán-execute flow funguje hladce: 6 explicitních rozhodnutí
  v plánu = 0 mid-session blockerů. Jediný drobný bump (Write
  guard po `alembic revision` skeletonu) byl vyřešen v 1 minutě
  bez side-effectu na DB.
- Inline `sa.table()` pattern je elegantní — schema lokalizovaný
  uvnitř migrace, parametrized inserts, ON CONFLICT idempotence.
  Když člověk migrace „dostane do ruky" jen jednou, obvykle to
  uvidíte jako verbose; když je vidíte 50 × při schema evolution
  later, pochopíte, proč decoupled-from-ORM je standardní pattern.
- KaTeX escape check uživatele byl preventivní — bez něj bych
  empiricky neověřil, že JSON round trip není double-escapnutý.
  Bind parametry to řeší automaticky, ale „věřit a ověřit" je
  pro thesis writeup hodnotnější než „věřit".
- Sloučení commits 3+4 (single „seed" commit místo empty marker)
  zajišťuje, že každý commit reprezentuje funkční change. Empty
  markers v session 004 by retrospektivně přidaly noise; v
  session 008 jsme se jim vyhnuli.

---

## Session 009 — 2026-04-29 — Backend evaluation API + KaTeX dependency

- **Prompt ID:** #9
- **Iterací plánu:** 1 (plán schválen napoprvé s explicit poznámkou
  o `not isinstance(answer, bool)` requirement)
- **Uživatelských zpráv v session:** 2 (prompt + plán schválení)
- **Commity v session:** 5 (přesně dle plánu)

### Cíl

Tři logicky propojené backend infrastructure změny + jeden frontend
dependency setup:
1. Sanitize `GET /api/lessons/{id}` payload — skrýt `correct_index`
   (multiple_choice) a `expected`/`tolerance` (numeric) z public response.
2. `POST /api/lessons/{id}/submit` — auth-required batch evaluation
   endpoint vracející per-exercise verdict + score summary.
3. KaTeX dependency setup pro frontend (žádný runtime use yet).

Žádné UI změny v této session, žádné DB změny.

### Co fungovalo na první pokus

- `sanitize_exercise_payload(exercise_type, payload)` helper — single
  source of truth pro „co je safe vystavit klientovi". Aplikováno
  v `get_lesson` přes explicit dict construction před `model_validate`.
  Empirický check potvrdil že MC payload obsahuje jen `options` a numeric
  je `{}`.
- 5 nových Pydantic schémat pro submit (AnswerSubmission,
  SubmissionRequest, ExerciseResult, ScoreSummary, SubmissionResponse).
- Submit endpoint flow (lesson lookup, set equality validation,
  per-answer evaluation, score aggregation) byl bez incidentu.
- Auth gate (`Depends(get_current_user)`) → 401 bez cookie ✓.
- Set inequality (chybějící odpověď) → 422 ✓.
- 404 na unknown lesson ✓.
- `npm install react-katex katex` na hostu prošel — react-katex 3.1.0
  + katex 0.16.45 v dependencies, peer dep auto-resolved.
- KaTeX CSS importovaný v `layout.tsx` přes `import "katex/dist/katex.
  min.css"` — bundlovaný do produkčního CSS chunku (80 KB CSS bundle
  obsahuje `font-family:KaTeX` selectors).

### Co bylo potřeba opravit

#### Bug: Pydantic 2 lax mode koercoval `true` → `1`, bypassing isinstance bool check

Test 7 v e2e ověření: submit `{"answer": true}` pro multiple_choice
exercise → očekávaný 422 → realita HTTP 200 s `user_answer: 1`,
`correct: true` (protože correct_index byl 1).

**Příčina:** `AnswerSubmission.answer: int | float | str` — Pydantic
2 v lax módu (default) koercuje JSON booleans na ints. `True` → `1`
(Python int) PŘED tím, než se _evaluate spustí. Můj `isinstance(
user_answer, bool)` check kontroloval `isinstance(1, bool)` → `False`.
Takže bool byl tichý okay.

**Fix:** `answer: StrictInt | StrictFloat | str` (Pydantic strict
variants). Strict variants reject bool at parse time. User submitter
`true` dostane structured 422 listing all three union arms (int,
float, str) a důvod neodmítnutí pro každý. Belt-and-suspenders:
runtime `isinstance(answer, bool)` v `_evaluate` zůstává jako
defensive check — pro případ že se schéma v budoucnu změní zpět.

**Lekce:** Pydantic 2 default lax coercion je friendly pro JSON
clients ale leakuje boolean → int conversion. Pro kritickou
type-discrimination logiku používat StrictInt/StrictFloat. User
explicit varoval v re-approval, ale praktické ověření přišlo až
v test 7 — přesně proto patří empirické testy do plánu.

### Rozhodnutí, která stojí za zaznamenání

- **Single `ExerciseResponse` + `sanitize_exercise_payload` helper**
  místo dvou Pydantic modelů (full vs public). Důvod: payload je
  `dict[str, Any]` — Pydantic shape jen vrchní vrstvy. Dva modely
  by jen zdvojily contract bez reálné type-safety výhody. Helper
  je 5 řádek, snadno se testuje, single source of truth.
- **Pydantic Union (`StrictInt | StrictFloat | str`) + runtime
  isinstance check**. Discriminated union by potřebovala discriminator
  field v request body — nemáme, exercise_type je inferovaný z DB
  lookupu. Strict variants reject bool early (cleanest), runtime
  check defensive ve `_evaluate`.
- **Set equality validation pro submitted exercise_ids.** Žádné
  chybějící, žádné navíc, žádné cizí UUID. 422 s `detail=
  "answers_must_match_lesson_exercises"`. Defenzivní — zajišťuje, že
  uživatel nemůže selektivně submitovat jen pohodlné odpovědi.
- **Auth split: GET veřejné, POST submit auth-required.** Read-only
  curriculum content nemá privacy sensitivity. Submit je per-user
  akce → JWT cookie required. Konzistentní s session 005 patternem
  pro auth-required state-changing endpointy.
- **Explanation v ExerciseResult bez ohledu na correctness.** Per
  user feedback: pedagogická hodnota explanation je v dokumentaci
  postupu, ne jen v opravě chyby. Uživatel co odpověděl správně
  stále chce vidět „proč" — utvrzení v technice.
- **Žádný progress write v této session.** `lesson_attempts`,
  `exercise_attempts` tabulky existují z session 004 ale write
  do nich přijde s persistencí (prompt #11+). Dnes čistě
  evaluation-without-side-effects.
- **react-katex (ne MathJax) jako math renderer.** Bundle size
  50 kB gz vs 200 kB, sync render bez FOUC, syntax coverage
  pokrývá 4MM101 prompts (`\lim`, `\frac`, `\infty`, super/sub-
  scripts). MathJax wider AMS-LaTeX support by byl unused weight.
- **Sanitization na serialization layer** (api/content.py),
  ne na model layer. Server interní logika čte `exercise.payload`
  raw přes ORM (potřebuje `correct_index` pro evaluation). Public
  expozice je oddělený concern — happens at HTTP response build
  time, ne na ORM property level.

### Použité verze (přírůstky)

| Komponenta | Verze |
|---|---|
| react-katex | 3.1.0 |
| katex | 0.16.45 |

### Verifikační výstupy

**Sanitization (per uživatelův explicit verifikační příkaz):**
```
$ curl /api/lessons/<lesson1> | jq '.exercises[0].payload'
{"options": [...]}                      # ✓ no correct_index

$ curl /api/lessons/<lesson1> | jq '.exercises[2].payload'
{}                                      # ✓ no expected, no tolerance
```

**Submit endpoint matrix (8 e2e cases):**
```
1. ALL CORRECT (3/3)               → 200, all_correct=true ✓
2. MIXED (1 correct, 2 wrong)      → 200, all_correct=false ✓
3. NUMERIC TOLERANCE (7.0001)      → correct=true (within 0.001) ✓
4. NUMERIC OUT OF TOLERANCE (7.01) → correct=false ✓
5. SET INEQUALITY (2 of 3 answers) → 422 ✓
6. TYPE MISMATCH (string for MC)   → 422 with detail ✓
7. BOOL FOR MC (true)              → 422 (Pydantic StrictInt rejection) ✓
8. UNKNOWN LESSON                  → 404 ✓
no auth (test 0)                   → 401 ✓
```

**KaTeX bundle:**
```
$ curl /_next/static/chunks/<hash>.css | grep -c 'font-family:KaTeX'
5+ matches                              # ✓ KaTeX styles in production CSS bundle
$ curl -sI /_next/static/chunks/<hash>.css | grep content-length
content-length: 80534                   # CSS bundle ~80 KB total
```

### Out of scope této session

- **Žádný UI rendering cvičení** — `/learn` zůstává placeholder.
  Lesson runner page (`/lesson/[id]`) přijde v promptu #10.
- **Žádné progress persistence** — write do `lesson_attempts`,
  `exercise_attempts` přijde s lesson runtime + per-user progress
  tracking v promptu #11+.
- **KaTeX deps installed, no usage yet** — InlineMath / BlockMath
  komponenty neimportuje žádný soubor. Až prompt #10 začne renderovat
  exercise prompts.
- **Tests odložené** — pokračování DoD deviation z session 005.
  E2e ověření přes curl s injected JWT pokrývá happy path
  + 7 edge cases.

### Dojem

- Plán-execute flow byl hladký až do testu 7 (bool rejection),
  který jsem v plánu měl jen jako mention ale ne jako test step.
  Připomenutí, že empirické testy chytí to, co type system
  v lax módu pustí.
- StrictInt fix je kompaktní (jeden import + jeden řádek schémy)
  ale významný — bez něj by byl celý bool defensive check ve
  `_evaluate` zbytečný theatre. Pydantic 2 lax coercion je past,
  která se v běžném code review snadno přehlédne.
- Sanitization helper je hezký example „security boundary at the
  serialization layer" patternu. Server-internal logic (evaluation)
  čte raw `correct_index`, public response ho strippuje. Žádné
  `if user_role == 'admin'` v jediné funkci — separation of concerns.
- KaTeX setup je explicitní příprava bez okamžitého use case. Pro
  thesis writeup: ukázka „add dependency in N-1 session, use it in N"
  patternu — odděluje setup risk (npm install conflicts, build
  break) od functionality risk (komponent rendering).
- Set equality validation pro answers je drobnost ale defenzivně
  cenná. Bez ní by uživatel mohl submitovat 2 z 3 odpovědí
  a dostat partial score, což je nepochopitelné pro lesson UX.

---

## Session 010 — 2026-04-29 — Lesson runner UI + progress persistence

- **Prompt ID:** #10
- **Iterací plánu:** 1 (plán schválen napoprvé; uživatel explicit
  ocenil návrh použít existující Streak + DailyActivity tabulky místo
  denormalizace na users — jeho původní brief navrhoval
  denormalizaci)
- **Uživatelských zpráv v session:** 2 (prompt + plán schválení)
- **Commity v session:** 10 plánovaných + 1 fix commit (@types/
  react-katex) = **11**

### Cíl

Postavit kompletní lesson runner UI napojený na content + submit
endpointy a přidat progress persistenci (lesson_attempts insert,
streak/daily_activity update). Po této session aplikace funguje
jako reálná aplikace — uživatel projde lekcí, dostane evaluaci
a uvidí svůj progress.

### Vlastní inženýrské rozhodnutí proti briefu (silná stránka pro thesis kapitolu 6)

Brief navrhoval denormalizovat streak / xp_today / last_activity_date
přímo na `users` tabulku. Pre-flight kontrola schématu odhalila, že
session 004 už designovala dvě dedikované tabulky **přesně pro tento
use case**:

- `streaks` (one row per user UNIQUE, current_length, longest_length,
  last_active_date)
- `daily_activities` (one row per user-day, xp_earned, lessons_completed)

Doporučení v plánu: **použít existující dedikované tabulky**.
Denormalizace na users by znamenala:
- Tři nové sloupce na `users` (migration drift)
- Dvě „zombie" tabulky bez writeru (ale s indexy a FK closure)
- Žádná auto-historie XP per den
- Ztráta `longest_length` (best streak ever — bonus feature zdarma
  z existujícího schématu)

Použité řešení:
- Streak upsert v submit endpointu (jeden řádek per user)
- DailyActivity upsert (jeden řádek per user-day; přirozený „xp_today
  reset" — nový den = nový řádek = 0 jako default)
- /me endpoint joins users → streak → daily_activity_today

Tato session je pěkný example, kdy plán-přezkum z mé strany odhalil
schémový mismatch v briefu. Schéma session 004 bylo postaveno
z předjímání budoucího requirements; pro thesis kapitolu 6 to ukazuje,
že vibe coding workflow s explicit plánovací fází zachycuje
schemu-implementation drift, který by jinak prošel bez povšimnutí.

### Co fungovalo na první pokus

- Migrace `add is_completed to lesson_attempts` autogenerated +
  manuální `server_default=false` doplnění (déjà vu z session 007).
  Apply prošel, partial UNIQUE index `WHERE is_completed = true`
  v DB.
- ORM Index v `__table_args__` se `postgresql_where=text("is_completed
  = true")` — autogenerate v budoucnu nebude flickovat tudíž drift.
- `GET /api/courses/{id_or_code}/progress` — JOIN přes
  lesson_attempts → lessons → sections, filtr `is_completed=true` +
  user.id → DISTINCT lesson_id list.
- Submit endpoint persistence: insert lesson_attempt + upsert
  streak + upsert daily_activity, vše v jedné transakci. Race
  handling přes `db.begin_nested()` savepoint + IntegrityError
  catch.
- E2e backend test sequence (8 cases): empty progress → 3/3 first
  completion → progress lists lesson → 3/3 replay (xp=0) → 1/2
  fail (xp=0, is_completed=false) → /me reflects state → DB
  inspection → cleanup. Všech 8 prošlo na první pokus.
- /me endpoint extension přes JOINs na streak + daily_activity_today.
- KaTeX renderer s naivní regex split + renderError fallback —
  rendruje 4MM101 obsah (`$\lim$`, `$\frac{0}{0}$`, atd.) bez
  problémů.
- Multiple choice + numeric exercise komponenty.
- LessonRunner state machine (answering → submitted) přes
  useState + useTransition.
- Result screen se 3-state XP message (per uživatelův dodatek):
  `xp_earned > 0` → "+10 XP", `is_completed && xp=0` → "Bez XP",
  `!is_completed` → "Pro získání XP potřebuješ ≥ 80 %".
- /learn page rewire: parallel fetch /me + structure + progress,
  per-section computeLessonState (sequential gating), render
  TopBar + path stones.

### Co bylo potřeba opravit

#### Bug: `react-katex` ships bez TS deklarací (commit `86cfc27`)

Frontend rebuild po commitu 9 selhal v TypeScript fázi:
```
Type error: Could not find a declaration file for module
'react-katex'. '/app/node_modules/react-katex/dist/react-katex.js'
implicitly has an 'any' type.
```

react-katex@3.x je plain JS bundle bez bundled `.d.ts`. Community
types existují pod `@types/react-katex` na DefinitelyTyped.

**Fix:** `npm install --save-dev @types/react-katex`. Build prošel
po druhém pokusu.

**Lekce:** Při instalaci npm balíčku v session 009 jsem ověřil, že
`react-katex` má bundled types (per moje memory). To bylo špatné —
verze 3.x je dropla. Should have run `npm run build` v session 009
jako smoke check.

### Rozhodnutí, která stojí za zaznamenání

- **Streak + DailyActivity tabulky** místo denormalizace (viz
  highlight section výše).
- **`is_completed` semantika**: `is_completed=true` jen u prvního
  ≥80% attemptu per user-lesson. Subsequent successful attempts
  jsou `is_completed=false` (i když score check prošel). Partial
  UNIQUE `WHERE is_completed = true` to vynucuje. Response
  `progress.is_completed` je naopak čistý score check (`≥80%`
  this attempt) — sémantika z user perspective.
- **Race handling přes savepoint** (`db.begin_nested()`) +
  IntegrityError catch. Zachovává outer transakci alive,
  retry s `is_completed=false, xp_earned=0`. Defensive — race je
  realisticky rare ale partial UNIQUE nás chrání před corruption.
- **xp_today „natural reset"**: nový UTC den = neexistuje
  daily_activity row pro dnes = SELECT vrátí NULL → 0. Žádný
  on-demand reset write potřeba.
- **UTC date assumption** pro „today" — Czech user submitující
  ve 00:30 SEČ je v 23:30 předchozího UTC dne. Akceptabilní pro
  thesis MVP. Per-user timezone preference může přijít s settings
  page.
- **Server action pro submit** přes `next/headers.cookies()` +
  manual cookie forward na backend. Discriminated union response
  (`{ok: true, data} | {ok: false, error}`) pro clean toast error
  path.
- **TopBar extracted z inline /learn header do
  `components/learn/top-bar.tsx`**. Reuse pro budoucí auth-required
  screens (settings, profile, leaderboard).
- **PathStone completed = Lucide Check icon** (size-9, strokeWidth=3)
  místo lesson number, accent green background. Konzistentní
  s Duolingo pattern.
- **3-state XP message v ResultScreen** (per uživatel feedback):
  pedagogická hodnota — uživatel vidí proč nedostal XP (replay vs.
  failed score).

### Použité verze (přírůstky)

| Komponenta | Verze |
|---|---|
| @types/react-katex | 3.0.4 |

### Verifikační výstupy

**Backend e2e (8 test cases):**
```
Test 1: empty progress                              ✓ {completed_lesson_ids: []}
Test 2: /me before submit                           ✓ streak=0, xp_today=0, last_activity=null
Test 3: lesson 1 first 3/3                          ✓ is_completed=true, xp=10, streak=1, xp_today=10
Test 4: progress now lists lesson 1                 ✓ length=1
Test 5: lesson 1 replay 3/3                         ✓ is_completed=true (score), xp=0 (already)
Test 6: lesson 2 1/2 = 50%                          ✓ is_completed=false, xp=0
Test 7: /me reflects all                            ✓ streak=1, xp_today=10, last_activity=2026-04-29
Test 8: lesson_attempts DB rows                     ✓ 3 rows (1 completed=true, 2 completed=false)
        streaks DB row                              ✓ current=1, longest=1, last_active=today
        daily_activities DB row                     ✓ today, xp_earned=10, lessons_completed=1
```

**Frontend e2e (HTML inspect přes injected JWT):**
```
/learn anon:                                        307 → /signin
/learn s cookie pre-submit:
  Section title "Limity funkce"                     ✓
  Greeting "Vítej, Tomáši!" (vokativ Tomáš → Tomáši) ✓
  1 lesson <Link href="/lesson/...">                ✓ (jen lesson 1)
  3 locked stones (Lock icons)                      ✓
/lesson/<id> s cookie:
  Progress counter "Cvičení 1 / 3"                  ✓
  KaTeX rendered classes                            ✓ (3 instances)
  "Pokračovat" button                               ✓
After submit lesson 1 (3/3 correct):
  /learn now: 2 lesson <Link>                       ✓ (lesson 1 completed + lesson 2 available)
  1 Check icon                                      ✓ (lesson 1 completed)
  2 Lock icons                                      ✓ (lesson 3, 4 locked)
  TopBar XP "10 / 20 XP"                            ✓ (visual; HTML grep masked by RSC fragmentation)
```

### Out of scope této session

- **`exercise_attempts` granular insert** — schema připraveno
  z session 004 ale write v této session vynechán. Brief explicit
  zmínka jako „vědomě odložená granularita" pro budoucí analytics.
- **Žádné UI pro replay confirmation** — uživatel může submitovat
  completed lesson znovu bez warning. Acceptable: zpráva
  „Bez XP — už jsi ji dokončil/a dříve" v result screen je
  dostatečný feedback.
- **Žádný retry/redo flow** v lesson runneru — pokud uživatel
  klikne Pokračovat moc rychle, žádný „Předchozí" button. Pro
  MVP linear flow akceptabilní.
- **UTC timezone assumption** — known limitation, dokumentováno
  v dev journal.
- **Tests odložené** — pokračování DoD deviation z session 005.
  E2e přes curl s injected JWT pokrývá happy path + edge cases.

### Dojem

- 10 plánovaných + 1 fix = 11 commitů. Jeden TypeScript dep miss
  (@types/react-katex) — odhalený až produkčním buildem, ne
  v session 009 kde jsem instaloval react-katex bez ověření TS
  resolution.
- Schéma-design rozhodnutí (Streak + DailyActivity vs. denormalizace)
  je nejcennější moment session pro thesis writeup. Pre-flight
  kontrola schématu před plánem odhalila mismatch s briefem;
  alternativní cesta byla nabídnuta a uživatel ji ocenil. To je
  přesně ten typ rozhodování, kde explicit planning fáze platí.
- Race handling přes savepoint (`db.begin_nested()`) je drobnost,
  ale eleganntní — zachovává outer transakci alive bez full rollback
  a re-fetch. Pro user-level race (concurrent tab submits) je to
  korektní behavior bez 500.
- 3-state XP message je drobné UX rozhodnutí ale s velkou
  pedagogickou hodnotou: uživatel rozumí PROČ nedostal XP.
  „Lekci jsi zvládl/a — bez XP" je friendlier než tichý 0 nebo
  generic „Nedosáhl/a jsi 80 %".
- Lesson runner state machine (answering → submitted) přes
  useState + useTransition + server action je idiomatický Next 15
  pattern. Žádný React Query, žádný Redux — local state stačí.
- KaTeX render naive regex split + renderError fallback je „good
  enough" pattern: pokrývá 100% našeho seedovaného obsahu, fail-safe
  pro edge cases. Kompletní LaTeX parser by byl overkill pro MVP.

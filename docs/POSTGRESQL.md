# PostgreSQL persistence and catalog search

## Native setup

Python 3.10+ and PostgreSQL 15+ are required; the measured environment uses Python 3.12
and PostgreSQL 18. Install PostgreSQL using your operating system's packages and start
its native service. Run the following from the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-test.txt
cp backend/.env.example backend/.env
```

Create a login and database as your PostgreSQL administrator (choose a deployment password):

```sql
CREATE ROLE jobsathi LOGIN PASSWORD 'jobsathi';
CREATE DATABASE jobsathi OWNER jobsathi;
```

Configure `DATABASE_URL` in `backend/.env`, then apply the versioned migrations before starting:

```bash
cd backend
../.venv/bin/python -m app.migrate
../.venv/bin/python -m app.import_jobs --file examples/jobs.json
../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The example is an explicitly labeled demonstration listing, never an automatic fallback.
Replace it with real employer/provider data for deployment. Health: http://127.0.0.1:8000/health
OpenAPI: http://127.0.0.1:8000/docs

The core dependency set supports catalog reads/imports, sessions and PDF rendering. For
the existing voice/LLM interview workflow, install `app/requirements.txt` and configure
`GEMINI_API_KEY`. ASR/LLM libraries load only on use. Run the frontend separately with
`npm install` and `npm run dev` from `frontend`; set `VITE_API_BASE_URL=http://localhost:8000`.

## Data and lifecycle

- `sessions` persists UUID sessions, answers, metadata, final profile and PDF filename.
  Answer appends are atomic JSONB updates, preventing concurrent lost answers. Completed
  profiles survive API restarts; repeat builds return the saved result.
- `jobs` stores deduplicated listings, canonical city, ISO country, active status, source,
  source URL, description, salary, publication date and generated search vector.
- `schema_migrations` records immutable SQL checksums and application time. An advisory
  transaction lock serializes migration runners. Any error rolls back the migration batch.
- PDF files and optional JSON exports remain under `RESUME_STORAGE_DIR` (default
  `backend/app/database`). Use persistent shared storage when running multiple API hosts;
  PostgreSQL stores metadata, not the PDF bytes. Back up both database and PDF storage.
- Existing JSON exports remain readable files; they are not silently imported into sessions.
  Historical uncompleted in-memory sessions were not durable and cannot be recovered.

`DATABASE_URL` is read when starting a pool or CLI, not at module import. Each API worker
owns a pool of 1–4 connections (`DATABASE_POOL_SIZE` controls the maximum). Pool acquisition
is bounded at five seconds / 32 waiters; SQL statements time out at ten seconds. Size the
sum of worker pools below PostgreSQL's connection limit. `/health` performs a database read;
connection/pool failures return 503 without connection credentials in the response.

## Import real jobs

Search never calls an external provider. A scheduled import refreshes the catalog:

```bash
cd backend
../.venv/bin/python -m app.import_jobs --file /absolute/path/to/jobs.json
../.venv/bin/python -m app.import_jobs --keywords Driver Delivery --location Bengaluru --city Bengaluru
```

The provider import uses configured Adzuna, Jooble and SerpAPI keys. It never imports the
legacy mock fallback. JSON input must be an array following `examples/jobs.json`; the
entire batch is validated and committed atomically. Reimporting the same normalized
title/company/city/country updates one row. `posted_at` is preserved unless explicitly
supplied. Set `is_active: false` to retire a listing. There is no automatic expiration.

`location` is the display string. Set `city` explicitly for provider strings such as
“Bengaluru, Karnataka, India”; otherwise the entire normalized display location becomes
the city key. Search accepts free-form profile strings, normalized with Unicode NFKC,
case folding and whitespace collapse; city matching is exact, not geocoding or substring
matching. “Bangalore” and “Bengaluru” are distinct unless normalized by the import source.

## Compatible API contract

The frontend's existing `{ "profile": finalProfile }` request remains valid:

```bash
curl --fail-with-body http://127.0.0.1:8000/search_jobs \
  -H 'Content-Type: application/json' \
  -d '{"profile":{"role":"Driver","skills":["Delivery"],"location":"Bengaluru"}}'
```

Response: `status`, `jobs`, `count` (returned page length), `next_cursor`. Each job keeps
the flat `title/company/location/description/salary/source/url/relevance_score` fields
and adds `id/posted_at`. Optional request fields: `country_code` (default `IN`), `limit`
(1–100, default 50), `cursor` (opaque value from the previous response). Empty matches
return an empty list, never invented vacancies. Validation errors use FastAPI's `detail`.

Existing profile-derived keyword generation and relevance scoring are reused. At most
eight role/skill/experience/education/certification keywords become `plainto_tsquery`
groups: words within a group are ANDed, groups are ORed. The `simple` dictionary preserves
Unicode lexemes without English stemming. Search covers title and description. Empty,
“India”, “null”, “none”, or “n/a” location omits the city filter; omitted keywords allow
active city/country browsing. Country and active filters always apply.

Catalog pages use deterministic newest-first order `(posted_at DESC, id DESC)` instead
of the legacy external aggregator's score ordering; the same relevance score is returned
for display. Keyset pagination avoids OFFSET scans and duplicate results when newer jobs
arrive between pages. A cursor is bound to the country/city/keywords and is rejected if
reused for a different search. Editing a listing's publication date can move it between
pages; pagination is not a cross-request snapshot. The separate employer mock API is
unrelated to this provider catalog.

## Tests and performance reproduction

Create a dedicated database whose name ends in `_test`. The test fixture truncates only
`jobs` and `sessions` there:

```bash
cd backend
export TEST_DATABASE_URL=postgresql://jobsathi:jobsathi@127.0.0.1:5432/jobsathi_test
../.venv/bin/python -m pytest -q
../.venv/bin/python -m ruff check app/persistence.py app/job_catalog.py app/import_jobs.py app/migrate.py tests benchmarks
```

Tests exercise real migrations, API filtering and response shape, Unicode search,
deduplication, generated-vector updates, rollback, injection resistance, cursors,
concurrent answer appends and interview/resume persistence across app restarts. The LLM
alone is mocked in the resume integration test; PostgreSQL and PDF rendering are real.
GitLab CI starts native PostgreSQL and runs the same suite.

For performance work create an **empty, dedicated** database ending in `_benchmark`.
The first migration intentionally contains only integrity indexes. Capture the baseline
before applying search indexes, using the same API process and unchanged dataset:

```bash
cd backend
export DATABASE_URL=postgresql://jobsathi:jobsathi@127.0.0.1:5432/jobsathi_benchmark
../.venv/bin/python -m app.migrate --target 1
../.venv/bin/python -m benchmarks.catalog_benchmark seed --rows 300000
../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8011 --no-access-log
```

In a second shell with the same `DATABASE_URL` and working directory:

```bash
../.venv/bin/python -m benchmarks.catalog_benchmark measure --phase before
# Only after before.json and its plans have been saved:
../.venv/bin/python -m app.migrate
../.venv/bin/python -m benchmarks.catalog_benchmark measure --phase after
../.venv/bin/python -m benchmarks.catalog_benchmark compare
```

The harness records all samples, SQL, parameters, result hashes, dataset checksums,
PostgreSQL settings, CPU/RAM, index definitions/sizes and EXPLAIN ANALYZE BUFFERS plans.
It refuses a baseline with search indexes and refuses comparisons with changed data,
queries or controlled settings. Warmup defaults to 10; measured requests to 100 per
query/path, one request at a time, alternating direct SQL and real HTTP. No artificial
delay, cache eviction, planner forcing or provider latency is included. Avoid other
builds/imports/load tests during both runs. See `backend/benchmarks/results` for evidence
and the performance report for conclusions and limitations.

## Deployment notes

Both local and Hugging Face entry points are `app.main:app` from a directory containing
`app/`. GitLab copies `backend/*` and `Dockerfile.hf`, preserving the package and migration
paths. Set a managed PostgreSQL `DATABASE_URL` and persistent `RESUME_STORAGE_DIR` in the
deployment environment. The Hugging Face launch command applies migrations before API
startup; other deployments should run the migration CLI as a release step.

Container configuration retains separate PostgreSQL, migration and API services plus
durable database/PDF volumes. Native PostgreSQL and local processes are the verification
path for this change; container builds/startup were not executed. Search-index creation
uses transactional DDL and locks catalog writes while building, so schedule a maintenance
window for a populated deployment. Never edit an already-applied migration: add a new
version. `--target` limits forward migration application; it does not downgrade a database.

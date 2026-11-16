# PostgreSQL catalog and persistence: implementation overview

- Author: Mathew Joseph
- Date: 2026-11-16
- Branch: `feat/postgresql-job-search`
- Implementation revision: `f7fb96a`

## Summary

JobSathi now stores interview sessions and job listings in PostgreSQL and serves
job search from an indexed local catalog. The implementation includes durable
session writes, repeatable migrations, validated imports, compatible search
responses, keyset pagination, and reproducible before/after measurements.

**Benchmark provenance: all 300,000 listings used for performance testing are
synthetic fixtures. They were generated locally, not collected from job boards.
The timings are real PostgreSQL and HTTP measurements on that synthetic dataset;
they are not production-traffic measurements.**

## Architecture and source map

```text
JSON file / configured job providers
    -> validation and normalization -> PostgreSQL jobs catalog

React profile -> POST /search_jobs -> bounded connection pool
    -> parameterized, indexed SQL -> relevance scores -> flat job-card response

Interview endpoints -> PostgreSQL sessions -> completed profile / PDF metadata
                                            -> PDF files on persistent storage
```

| Component | Implementation |
| --- | --- |
| Connection pool and interview persistence | `backend/app/persistence.py` |
| Search request/response models, normalization, ingestion, pagination | `backend/app/job_catalog.py` |
| File/provider import CLI | `backend/app/import_jobs.py` |
| Application lifecycle, interview endpoints, database health | `backend/app/main.py` |
| Checksummed migration runner | `backend/app/migrate.py` |
| Baseline schema | `backend/app/migrations/001_persistence.sql` |
| Search indexes | `backend/app/migrations/002_job_search_indexes.sql` |
| Synthetic data generator | `backend/benchmarks/seed.sql` |
| SQL/HTTP measurement and comparison harness | `backend/benchmarks/catalog_benchmark.py` |

## Persistence and operational behavior

- `sessions` stores UUIDs, JSONB answers and metadata, completed profiles, and PDF
  filenames. Answer appends are atomic database updates. Completed profiles survive
  API restarts; a repeated profile-build request returns the saved result.
- `jobs` stores normalized listing identity, display location, canonical city,
  country, active status, source/application URL, description, salary, publication
  time, and a stored `simple` full-text vector over title and description.
- `schema_migrations` records migration versions and SHA-256 checksums. A
  transaction-scoped advisory lock serializes runners; a failed batch rolls back.
  Previously applied SQL cannot be silently modified.
- Each API worker owns a bounded pool, defaulting to 1–4 connections. Acquisition
  allows five seconds and at most 32 waiters; statements have a ten-second timeout.
  Database connection/pool failures return a sanitized HTTP 503 response.
- `DATABASE_URL` or separate libpq environment variables configure connections.
  Separate credentials safely support special characters in passwords.
- PDF bytes remain under `RESUME_STORAGE_DIR`; PostgreSQL stores their metadata.
  A deployment therefore needs both durable database storage and durable PDF storage.

## Search and import behavior

The existing frontend request remains supported:

```json
{
  "profile": {
    "role": "Professional Driver",
    "location": "Bengaluru, Karnataka",
    "skills": ["Two Wheeler Driving", "Customer Communication"]
  },
  "limit": 50
}
```

The response contains `status`, `jobs`, `count`, and `next_cursor`. Job cards retain
their flat fields and add `id` and `posted_at`. The default page size is 50, bounded
to 1–100; `count` describes the returned page.

City normalization is shared by imports and queries, including city-first
comma-separated locations and known aliases such as Bangalore/Bengaluru. Explicit
roles take priority over experience-role and skill fallbacks. Generic modifiers
such as “Professional” are removed. Previous employer names do not broaden
occupational eligibility.

Active status, country, city, and occupational text are filtered **before** the
page limit. Results are newest-first by `(posted_at DESC, id DESC)`; relevance
scores explain eligible matches rather than globally sorting the catalog. Cursors
are tied to the search criteria and use the date/ID pair instead of OFFSET.

Search reads the database without calling job providers. The import CLI accepts
local JSON or configured Adzuna, Jooble, and SerpAPI results. Invalid provider
records are skipped with explicit counts and reasons; invalid local JSON input
rejects the batch. Valid records are written atomically and deduplicated by
normalized title/company/city/country. Real vacancies must be imported separately;
the benchmark generator and demonstration listing are explicitly synthetic.

## Index design

Migration 001 creates only integrity indexes. Migration 002 adds:

```sql
CREATE INDEX jobs_active_city_recent_idx
ON jobs (country_code, city_key, posted_at DESC, id DESC)
WHERE is_active;

CREATE INDEX jobs_active_country_recent_idx
ON jobs (country_code, posted_at DESC, id DESC)
WHERE is_active;

CREATE INDEX jobs_active_search_document_idx
ON jobs USING gin (search_document)
WHERE is_active;
```

The composite indexes align equality filters with newest-first ordering, allowing
PostgreSQL to stop after finding a page of eligible rows. The country-only variant
supports searches without a city. The partial GIN index supports selective or
no-match text searches; it was not responsible for the measured popular-term gains.

## Benchmark dataset and measured results

`backend/benchmarks/seed.sql` uses PostgreSQL `generate_series` to create 300,000
rows. Hash-derived assignments select from 12 occupation titles and 20 Indian city
labels. Employers are named `Synthetic employer <number>`; application URLs use
`https://example.invalid/jobs/`. Descriptions repeat a fixed paragraph, salary is
fixed, 10% of rows are inactive, and every 23rd row has country `US`. This is a
controlled fixture, not a representative sample of live vacancies.

Measurements used native PostgreSQL 18.7, one Uvicorn worker, one sequential
client, warm caches, ten warmups, and 100 samples per SQL/HTTP workload. The final
implementation was measured first on a fresh integrity-index-only database, then
again after adding search indexes. Dataset, query, response, source, and relevant
configuration fingerprints matched between phases.

| HTTP workload | Before median / p95 | Indexed median / p95 | Median improvement |
| --- | --- | --- | --- |
| Multi-field frontend Driver profile | 55.965 / 64.462 ms | 3.329 / 3.702 ms | 16.81× |
| Driver, Bengaluru | 55.454 / 64.921 ms | 3.163 / 3.496 ms | 17.53× |
| Plumber, Pune | 57.819 / 75.415 ms | 3.305 / 3.560 ms | 17.49× |
| Electrician, India | 56.806 / 64.680 ms | 3.408 / 3.760 ms | 16.67× |

For the primary workload, direct SQL median improved from **53.202 to 1.026 ms**.
The captured plan changed from a parallel full scan and top-N sort to an ordered
composite-index scan. Shared buffers touched fell from 50,276 to 294. The three
indexes added approximately 31.23 MiB; their build and statistics refresh took
1.461 seconds on this dataset.

These results establish local single-client improvement on the stated fixture.
They do not establish production concurrency, cold-cache latency, live-provider
latency, or behavior under real vacancy distributions. Raw final-code evidence is
in `backend/benchmarks/results/review/`; the parent results directory retains
earlier measurements and must not be mixed with the final comparison.

## Verification and rollout

**25 backend tests passed**, with Ruff, compilation, and whitespace checks also
passing. Coverage includes realistic frontend profiles, city aliases, pre-limit
eligibility, pagination, SQL parameterization, ingestion rollback/deduplication,
credential handling, concurrent answer appends, durable sessions, and actual PDF
generation. Provider/LLM calls used fixtures; PostgreSQL and PDF generation were
real. Heavy ASR and container execution were not exercised.

The backend test job is configured in `.gitlab-ci.yml`; this is a local validation
record, not a claim that a GitHub Actions run completed.

For deployment:

1. Provision PostgreSQL and configure connection settings and persistent PDF storage.
2. Install the appropriate backend dependencies and run `python -m app.migrate`
   from `backend` before starting the API.
3. Import actual catalog data using `python -m app.import_jobs`; start
   `uvicorn app.main:app` and check `/health`.
4. Plan index creation around write traffic: the migration uses transactional DDL
   and blocks catalog writes during its build. Listing retirement/import scheduling
   is an operational responsibility; listings do not automatically expire.

Detailed setup, API, test, and baseline-first reproduction commands:
`docs/POSTGRESQL.md`.

Full measurement methodology, environment, explain plans, and limitations:
`docs/PERFORMANCE.md`.

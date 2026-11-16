# PostgreSQL catalog search: measured index improvement

Measured on **2026-11-16**, authored by **Mathew Joseph**.

## Final-code outcome

The realistic frontend profile search improved from **55.965 ms to 3.329 ms HTTP median
(16.81×)**. Its HTTP p95 fell from **64.462 ms to 3.702 ms**. The highest indexed HTTP
p95 across all four workloads was **3.760 ms**, below the 180 ms read-path target
**under the tested single-client, warm-cache conditions**. Baseline p95 was already
below that target; indexing provides the measured relative improvement.

| Search (50 results) | SQL before median / p95 | SQL after median / p95 | HTTP before median / p95 | HTTP after median / p95 | HTTP median gain |
|---|---:|---:|---:|---:|---:|
| Frontend Professional Driver, Bengaluru/Karnataka | 53.202 / 63.149 ms | 1.026 / 1.144 ms | 55.965 / 64.462 ms | 3.329 / 3.702 ms | 16.81× |
| Driver, Bengaluru | 53.172 / 63.105 ms | 0.985 / 1.240 ms | 55.454 / 64.921 ms | 3.163 / 3.496 ms | 17.53× |
| Plumber, Pune | 55.659 / 78.436 ms | 1.275 / 1.468 ms | 57.819 / 75.415 ms | 3.305 / 3.560 ms | 17.49× |
| Electrician, all India | 53.787 / 60.877 ms | 1.282 / 1.468 ms | 56.806 / 64.680 ms | 3.408 / 3.760 ms | 16.67× |

All figures derive from recorded individual samples, not EXPLAIN estimates. p95 is
nearest-rank over 100 measurements per query/path. Values are rounded only for display;
speedups are calculated from unrounded medians. Generated table:
`backend/benchmarks/results/review/comparison.md`.

This compares the same real PostgreSQL catalog read path before and after indexing.
External-provider aggregation is outside the measured request. No artificial delays,
planner forcing or server tuning were used.

## Correctness and measurement chronology

The first implementation and its measurements remain in commits `3de90d4` and `af44eaa`,
with documentation clarification `925429d`. Review then identified city/state parsing,
generated-role matching and employer-driven eligibility defects. These changed query
semantics, so **the earlier 17.37× result is historical, not evidence for final code**.
The original database and all original samples/plans remain intact under
`backend/benchmarks/results/`; the new evidence is isolated in its `review/` subdirectory.

Final-code sequence:

1. Corrected shared city normalization, role-led eligibility before `LIMIT`, and scoring
   with the same tsquery. Added regressions using the supplied demo listing and a realistic
   generated resume, including 60 newer unrelated listings that must not displace one
   older relevant driver. All 25 tests passed before measuring.
2. Created a **fresh** native database, `jobsathi_review_benchmark`, on the existing
   PostgreSQL 18.7 server. Applied migration 001 only (primary key and identity uniqueness).
3. Seeded 300,000 deterministic listings once and ran `VACUUM (ANALYZE) jobs`. Started a
   fresh Uvicorn process with the final implementation at http://127.0.0.1:8012.
4. Captured baseline at **08:34:30–08:35:24 UTC**, before applying any search indexes to
   this database. The harness verified only the two integrity indexes existed.
5. Applied unchanged migration 002 at **08:35:38–08:35:39 UTC**. Three search indexes plus
   `ANALYZE` took **1.461 seconds**; raw build timing is recorded separately.
6. Captured indexed measurements at **08:35:46–08:35:50 UTC**, with the same still-running
   API, dataset, SQL, parameters, pool, client, warmups, repetitions and settings.
7. Comparison verified matching dataset/response hashes, source hashes, query SQL/parameters,
   heap size, hardware, Python/PostgreSQL versions and controlled PostgreSQL settings.

No interrupted or partial runs are included. Code hashes for the catalog, scoring module,
pool configuration and benchmark harness are saved in both phase JSON files.

## Realistic primary request and selection

```json
{
  "profile": {
    "name": "Arun Kumar",
    "role": "Professional Driver",
    "location": "Bengaluru, Karnataka",
    "skills": ["Two Wheeler Driving", "Customer Communication"],
    "experience_years": 3,
    "experience_details": [{"role": "Delivery Driver", "company": "Acme Logistics"}],
    "education": [{"degree": "Secondary School"}],
    "certifications": ["Driving Licence"],
    "languages": ["Kannada", "Hindi"]
  },
  "limit": 50
}
```

Both phases normalize this to role `driver` and city `bengaluru`. Prior employer names
and ancillary skills do not broaden an explicit role into unrelated occupations.
The same parameterized query used by the live API and EXPLAIN filters active IN listings,
city and occupational text **before** the recency/keyset limit. Eligibility scores use
the same tsquery; remaining profile bonuses are computed on eligible results. Every
primary response contains 50 matching listings. Full SQL, parameters and response hashes
are in the evidence JSON files. Selection/ranking details are in `docs/POSTGRESQL.md`.

## Hardware and runtime

| Item | Actual environment |
|---|---|
| CPU | AMD Ryzen 7 4800H with Radeon Graphics, 16 logical CPUs |
| RAM | 7,520,316 KiB total (~7.17 GiB); available 2,848,596 KiB before / 2,986,588 KiB after |
| Storage | KLEVV CRAS C715 M.2 NVMe SSD 1TB; PostgreSQL data on Btrfs `/dev/nvme1n1p4` |
| OS | Linux 7.3.1-1-cachyos x86_64, glibc 2.44 |
| Database | PostgreSQL 18.7, native local process, TCP port 55432 |
| Application | Python 3.12.14; FastAPI 0.163.1; Psycopg 3.3.9; psycopg-pool 3.3.3; Uvicorn 0.54.0 |
| HTTP client | HTTPX 0.28.1, persistent TCP connection to http://127.0.0.1:8012 |
| Concurrency | One measured request at a time; one Uvicorn worker; pool min 1 / max 4 |
| Memory settings | `shared_buffers=128MB`, `work_mem=4MB`, `maintenance_work_mem=64MB`, `effective_cache_size=4GB` |
| Planning | `max_parallel_workers_per_gather=2`, `default_statistics_target=100`, JIT on |
| Costs | `random_page_cost=4`, `seq_page_cost=1`; sequential/index/bitmap scans all enabled |
| Durability | fsync, synchronous_commit, full_page_writes on; max_connections 30 |

The exact installed packages are in `backend/benchmarks/results/review/python-packages.txt`.
Both phases use `prepare_threshold=None`, planning for actual optional filters rather
than switching to a generic prepared plan. No settings differ between phases.

## Dataset and workload controls

- **Synthetic, not real vacancies:** 300,000 rows, 20 city labels, 12 blue-collar titles,
  unique synthetic employers and example.invalid source URLs. Descriptions repeat an
  operations/training paragraph three times. Hash-derived city and role distributions
  are independent of recency; recent rows are not constructed to favor the primary query.
  10% of rows are inactive; every 23rd row has country US.
- Heap: **409,600,000 bytes (390.625 MiB)** before and after. The stored `simple` tsvector
  exists in both phases. Seed SHA-256 is recorded; the seed is unchanged from the first run.
- Dataset fingerprint: `rows=300000`, `id_sum=45000150000`,
  `content_checksum=3178161630766776571823` (sum of PostgreSQL hashes of complete rows,
  including generated vectors). Checksums and returned-page SHA-256 hashes match.
- Ten alternating SQL/HTTP warmups precede 100 alternating measured SQL/HTTP reads per
  query per phase: eight 100-sample series each phase. SQL fetches 51 rows to detect the
  next page; the API returns 50. No provider or LLM runs on the measured read path.
- Direct SQL timing includes driver round trip, execution and materializing 51 rows.
  HTTP includes real TCP, routing/dependencies, pool checkout, SQL, scoring, response
  validation/serialization, transfer and client JSON decoding.
- EXPLAIN ANALYZE runs after timings, separately in JSON and readable text. Its execution
  times are diagnostic samples, never substitutes for observed HTTP request latency.
- Cache policy: warm, no OS/PostgreSQL eviction. The heap exceeds shared_buffers, so
  sequential scans report PostgreSQL buffer reads even when the OS caches the pages.
  Index building warms some pages, followed by identical workload warmups in both phases.

## Why the indexes help

Before indexing, the primary plan is `Parallel Seq Scan → top-N Sort → Result → Gather
Merge → Limit`. It touches **50,276 shared buffers** (16,086 hits / 34,190 reads). Three
processes scan the whole catalog; each rejects roughly 99,264 rows. Sorting must inspect
all matches to determine the newest page.

After indexing, it is `Index Scan using jobs_active_city_recent_idx → Limit`:

```sql
CREATE INDEX jobs_active_city_recent_idx
ON jobs (country_code, city_key, posted_at DESC, id DESC)
WHERE is_active;

CREATE INDEX jobs_active_country_recent_idx
ON jobs (country_code, posted_at DESC, id DESC)
WHERE is_active;
```

Equality columns lead; date/id match ordering and the keyset boundary. The partial
predicate excludes inactive listings. PostgreSQL stops after 51 matching candidates
without a global sort. The primary indexed plan examines 289 rows (51 returned, 238
text rejects), touching **294 buffers**. Plumber/Pune touches 534; country-wide Electrician
uses the country/recency index and touches 563. The city-prefixed index cannot provide
country-wide recency ordering.

The partial GIN `jobs_active_search_document_idx` supports selective/no-match terms.
It is not selected for these four popular-term pages and receives no credit for their
speedups. A supplementary Astronaut/Bengaluru diagnostic selects its bitmap scan and
executes in 0.131 ms; that one sample has no baseline and is not a latency comparison.

## Costs and limitations

- Indexes grow from **29,556,736 to 62,308,352 bytes**, adding **32,751,616 bytes (~31.23 MiB)**:
  city/recency 13,557,760; country/recency 10,977,280; GIN 8,216,576. Writes maintain three
  extra indexes; write throughput and GIN pending-list behavior were not measured.
- Migration 002 uses transactional index creation, blocking catalog writes during the
  build. Its observed 1.461 seconds is not a production guarantee.
- Shared development hardware, local warm caches and concurrency one do not establish
  a production SLA, cold-start/WAN latency, high-concurrency tails, rare-term pagination
  or multi-million-row scaling. Synthetic repeated text does not reproduce real vacancy
  skew. Validate representative production distributions and ingestion rates separately.
- Native PostgreSQL/API/PDF paths are exercised. Configuration/password tests parse YAML
  and round-trip conninfo; no Docker command or container runtime verification is used.
  Paid providers, LLM and heavy ASR are not executed; provider/LLM fixtures are mocked.
- Starlette emits a non-failing deprecation warning for its HTTPX TestClient adapter.
  Timing uses independent real HTTPX TCP requests.

## Reproduce and inspect

Use the native commands in `docs/POSTGRESQL.md` with a fresh `_benchmark` database and
a new output directory. `--target 1` does not remove existing indexes. The harness
rejects already-indexed baselines and refuses to overwrite phase evidence. Keep other
builds, imports and load tests idle during both phases; real timings will vary.

Current evidence in `backend/benchmarks/results/review/`:

- `before.json`, `after.json`: all samples, requests/SQL, hashes, hardware and settings.
- `before-*.plan.json` / `after-*.plan.json`: structured EXPLAIN ANALYZE BUFFERS SETTINGS.
- `before-*.plan.txt` / `after-*.plan.txt`: independently captured readable plans.
- `comparison.md`: generated medians/p95, speedups and comparison validation.
- `index-build.json`, `index-sizes.json`: build chronology and measured index storage.
- `after-no-match.plan.txt`: supplementary GIN diagnostic.
- `python-packages.txt`: installed dependency versions.

Historical first-pass files remain unchanged in the parent evidence directory; do not
mix their SQL, requests or timings with this final-code comparison.

# PostgreSQL catalog search: measured index improvement

Measured on **2026-11-16**, authored by **Mathew Joseph**.

## Outcome

The primary Driver/Bengaluru search improved from **55.400 ms to 3.190 ms HTTP median
(17.37×)**. Its HTTP p95 fell from **71.892 ms to 4.650 ms**. The highest indexed HTTP
p95 across the three measured searches was **5.106 ms**, below the 180 ms read-path
target **under the tested single-client, warm-cache conditions**.

These results compare the PostgreSQL catalog before and after indexing. The measured
baseline excludes external-provider aggregation, artificial delays and forced query
plans.

| Search (50 results) | Direct SQL before median / p95 | Direct SQL after median / p95 | HTTP before median / p95 | HTTP after median / p95 | HTTP median gain |
|---|---:|---:|---:|---:|---:|
| Driver, Bengaluru | 52.886 / 71.924 ms | 0.950 / 1.579 ms | 55.400 / 71.892 ms | 3.190 / 4.650 ms | 17.37× |
| Plumber, Pune | 65.120 / 88.230 ms | 1.136 / 1.918 ms | 68.246 / 83.104 ms | 3.405 / 5.034 ms | 20.04× |
| Electrician, all India | 65.235 / 79.541 ms | 1.091 / 1.929 ms | 68.360 / 79.697 ms | 3.358 / 5.106 ms | 20.36× |

All figures come from recorded individual samples, not EXPLAIN estimates. p95 is the
nearest-rank percentile of 100 measurements per query/path. The companion generated
table is `backend/benchmarks/results/comparison.md`.

## Genuine baseline-first sequence

1. Implemented PostgreSQL persistence and the real `/search_jobs` API. Applied only
   `backend/app/migrations/001_persistence.sql`: jobs primary key and identity uniqueness
   indexes, with no city, recency or full-text indexes.
2. Seeded 300,000 listings once, then ran `VACUUM (ANALYZE) jobs`.
3. Captured baseline at **08:04:39–08:05:25 UTC**. Stored raw samples, environment,
   query text/parameters, dataset/result fingerprints and explain plans.
4. Committed that tested implementation and baseline as **`3de90d4`**. The search-index
   migration did not exist in that commit.
5. Added and applied migration 002 at **08:09:24–08:09:26 UTC**. Creating the three indexes
   and refreshing statistics took **1.612 seconds** in total.
6. Captured the indexed run at **08:09:31–08:09:35 UTC**, using the same still-running
   Uvicorn process, database, queries, client settings, warmups and sample counts.
7. The comparison command verified identical dataset fingerprints, SQL, parameters,
   response hashes, PostgreSQL settings, Python version, hardware and heap size.

The host restarted before database testing began; it did not interrupt either recorded
benchmark. Failed dependency downloads and the initial database-unavailable test run
are not included in timing samples.

## Hardware and runtime

| Item | Actual environment |
|---|---|
| CPU | AMD Ryzen 7 4800H with Radeon Graphics, 16 logical CPUs |
| RAM | 7,520,316 KiB total (~7.17 GiB); available 3,022,380 KiB before / 2,846,524 KiB after |
| Storage | KLEVV CRAS C715 M.2 NVMe SSD 1TB, PostgreSQL data on Btrfs `/dev/nvme1n1p4` |
| OS | Linux 7.3.1-1-cachyos x86_64, glibc 2.44 |
| Database | PostgreSQL 18.7, native local process, TCP port 55432 |
| Application | Python 3.12.14; FastAPI 0.163.1; Psycopg 3.3.9; psycopg-pool 3.3.3; Uvicorn 0.54.0 |
| HTTP client | HTTPX 0.28.1, persistent connection to http://127.0.0.1:8011 |
| Concurrency | One measured request at a time; one Uvicorn worker; pool min 1 / max 4 |
| PostgreSQL memory | `shared_buffers=128MB`, `work_mem=4MB`, `maintenance_work_mem=64MB`, `effective_cache_size=4GB` |
| Planning | `max_parallel_workers_per_gather=2`, `default_statistics_target=100`, JIT on |
| Costs | `random_page_cost=4`, `seq_page_cost=1`; sequential/index/bitmap scans all enabled |
| Durability | fsync, synchronous_commit and full_page_writes all on; max_connections 30 |

Full dependency versions are in `backend/benchmarks/results/python-packages.txt`.
Both runs used the same pool settings, including `prepare_threshold=None`: each query
is planned for its actual optional filters, avoiding generic prepared plans. No
`enable_seqscan=off`, cost overrides or server tuning were used to manufacture a gain.

## Dataset and workload controls

- **Synthetic, not real vacancies:** 300,000 rows, 20 Indian city labels, 12 blue-collar
  role titles, unique synthetic employers and example.invalid source URLs. Descriptions
  repeat a fixed operations/training paragraph three times. City and role are assigned
  independently of recency via deterministic hashes, so recent rows are not deliberately
  clustered to match the primary query. 10% are inactive; every 23rd row has country US.
- Heap: **409,600,000 bytes (390.625 MiB)** in both phases. Stored `simple` tsvectors were
  already present before indexing. The SQL seed and its SHA-256 are recorded.
- Data fingerprint in both runs: `rows=300000`, `id_sum=45000150000`,
  `content_checksum=3178161630766776571823` (sum of PostgreSQL hashes of complete rows,
  including generated vectors). Every returned page's SHA-256 also matched.
- Each request uses the same profile, default country IN and limit 50. SQL fetches 51
  rows to detect another page. Results order by `(posted_at DESC, id DESC)`.
- Ten alternating SQL/HTTP warmups precede 100 alternating measured SQL/HTTP reads for
  each query in each phase. Each phase has six 100-sample series. The same API process served
  both phases; no network provider or LLM was called.
- Direct SQL timing includes driver round trip, query and materializing all 51 rows.
  HTTP timing includes TCP request/response, route/dependency processing, pool checkout,
  SQL, relevance scoring, response validation/serialization and client JSON decoding.
- EXPLAIN ANALYZE runs **after** timed measurements, separately in JSON and readable text.
  Their execution times are diagnostic samples and are not substituted for HTTP timings.
- Cache policy: warm, no explicit OS/PostgreSQL cache eviction. The heap exceeds
  shared_buffers, so repeated sequential scans still report PostgreSQL buffer reads;
  these are not proof of physical disk reads because the OS may cache them. Index
  construction warms some pages, followed by identical workload warmups in both phases.

## Why the composite indexes help

The planner chose `Parallel Seq Scan → Sort (top-N heapsort) → Gather Merge → Limit`
before indexing. Driver/Bengaluru scanned the full catalog with three processes and
touched **50,090 shared buffers** in the captured text plan (15,915 hits / 34,175 reads).
Each process discarded roughly 99,264 rows. Sorting still examined all matches to find
the newest page.

After indexing it chose `Index Scan using jobs_active_city_recent_idx → Limit`:

```sql
CREATE INDEX jobs_active_city_recent_idx
ON jobs (country_code, city_key, posted_at DESC, id DESC)
WHERE is_active;

CREATE INDEX jobs_active_country_recent_idx
ON jobs (country_code, posted_at DESC, id DESC)
WHERE is_active;
```

Equality-filter columns come first; descending date/id provide the requested order and
keyset boundary. The partial predicate excludes inactive listings. PostgreSQL can stop
after 51 text matches without scanning/sorting all matches. The primary after-plan
examined 289 candidate rows (51 returned, 238 text rejects) and touched **294 buffers**.
Plumber/Pune touched 534 buffers. Country-wide Electrician used the second composite
index, touching 563 buffers; a city-prefixed index cannot provide global recency order.

The `jobs_active_search_document_idx` partial GIN index supports selective/no-match text
queries. It was **not** chosen for the three popular-term top-page measurements and is
not credited with their speedups. A supplementary Astronaut/Bengaluru EXPLAIN selected
its bitmap index scan and returned no results in 0.080 ms execution time. This single
diagnostic sample has no baseline counterpart and is **not** a latency comparison.

## Cost and limitations

- Job indexes grew from **29,556,736 bytes to 62,308,352 bytes**, an additional
  **32,751,616 bytes (~31.23 MiB)**: city/recency 13,557,760 bytes, country/recency
  10,977,280 bytes, GIN 8,216,576 bytes. Each listing write maintains three extra indexes;
  write throughput and GIN pending-list behavior were not benchmarked.
- Migration 002 uses transactional index creation, blocking catalog writes during its
  build. The observed 1.612-second build on this dataset is not a production guarantee.
- These are local, warm-cache, single-client measurements on a shared development
  machine. They do not establish a production SLA, cold-start behavior, WAN latency,
  high-concurrency tails, rare-term paging or multi-million-row scaling. Read p95 below
  180 ms is demonstrated only for the stated workload, not every endpoint.
- The synthetic distribution and repeated text do not reproduce real vacancy skew.
  Validate production query plans and import/write rates with representative data.
- Native PostgreSQL, API and PDF paths were exercised. Container configuration was
  syntax-checked only; no container build/startup was performed. The heavy ASR model and
  paid LLM/provider calls were not executed; the resume integration test mocks the LLM.
- The test runner emits a non-failing Starlette warning that its HTTPX TestClient adapter
  is deprecated. The performance harness uses independent real HTTPX TCP requests.

## Reproduce and inspect

Follow the native setup and exact baseline-first commands in `docs/POSTGRESQL.md`.
Use a fresh `_benchmark` database: `--target 1` does not remove indexes from an existing
database, and the harness rejects an already-indexed baseline. Keep other builds,
imports and load tests idle during measurement. Actual wall-clock values will vary.

Evidence under `backend/benchmarks/results/`:

- `before.json`, `after.json`: raw samples, exact requests/SQL, fingerprints and settings.
- `before-*.plan.json` / `after-*.plan.json`: structured EXPLAIN ANALYZE BUFFERS SETTINGS.
- `before-*.plan.txt` / `after-*.plan.txt`: independently captured readable plans.
- `comparison.md`: generated medians/p95 and checked-comparison summary.
- `index-build.json`, `index-sizes.json`: real build chronology and storage overhead.
- `after-no-match.plan.txt`: supplementary GIN/no-match diagnostic.
- `python-packages.txt`: exact installed Python package versions.

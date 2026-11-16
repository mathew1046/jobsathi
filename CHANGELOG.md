# Changelog

## 2026-11-16 — Frontend-compatible matching and verified final-code performance

Author: Mathew Joseph · Commit reference: `925429d` (base)

- Normalize city/state and generated roles consistently; enforce role-led eligibility
  before paging, retain scoring bonuses, and explicitly count skipped provider records.
- Pass separate database credentials safely; 25 focused/native integration tests pass.
- Fresh 300,000-listing baseline-first run: realistic frontend HTTP median 55.965 →
  3.329 ms (16.81×), p95 64.462 → 3.702 ms; preserve initial evidence as history.

## 2026-11-16 — Performance report scope

Author: Mathew Joseph · Commit reference: `af44eaa` (base)

- Clarify that the performance comparison measures the local PostgreSQL catalog
  under the documented workload and excludes external-provider aggregation.
- Keep the report focused on recorded measurements and reproducible conditions.

## 2026-11-16 — Indexed catalog search and measured performance

Author: Mathew Joseph · Commit reference: `3de90d4` (base)

- Add active-only city/country composite recency indexes and a full-text GIN index after
  committing the genuine 300,000-listing PostgreSQL baseline.
- Identical primary HTTP search improves 55.400 → 3.190 ms median (17.37×), p95
  71.892 → 4.650 ms; publish raw samples, explain plans, hardware, costs and limitations.
- Preserve identical query/data/result fingerprints and verify the integration suite
  with indexed migrations; no artificial delays or planner forcing.

## 2026-11-16 — PostgreSQL persistence and measured search baseline

Author: Mathew Joseph · Commit reference: `0e4c8eb` (base)

- Persist interview sessions, answers, resume metadata and imported job listings in PostgreSQL;
  serve compatible, bounded catalog search through the real API with keyset pagination.
- Add checksummed migrations, native PostgreSQL integration CI, deployment configuration and
  a reproducible 300,000-listing baseline: Driver/Bengaluru HTTP median 55.400 ms, p95 71.892 ms.
- Fifteen integration tests pass; raw SQL/HTTP samples and explain plans were captured before
  adding search indexes. Native setup and operational limitations are documented.

# Changelog

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

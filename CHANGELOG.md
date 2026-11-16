# Changelog

## 2026-11-16 — PostgreSQL persistence and measured search baseline

Author: Mathew Joseph · Commit reference: `0e4c8eb` (base)

- Persist interview sessions, answers, resume metadata and imported job listings in PostgreSQL;
  serve compatible, bounded catalog search through the real API with keyset pagination.
- Add checksummed migrations, native PostgreSQL integration CI, deployment configuration and
  a reproducible 300,000-listing baseline: Driver/Bengaluru HTTP median 55.400 ms, p95 71.892 ms.
- Fifteen integration tests pass; raw SQL/HTTP samples and explain plans were captured before
  adding search indexes. Native setup and operational limitations are documented.

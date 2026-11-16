"""Import a JSON catalog or configured provider results, outside the read path."""

import argparse
import json
from pathlib import Path

from pydantic import ValidationError

from app.job_catalog import JobInput, JobRepository
from app.job_search import (
    ADZUNA_APP_ID,
    ADZUNA_APP_KEY,
    JOOBLE_KEY,
    SERPAPI_KEY,
    fetch_adzuna,
    fetch_jooble,
    fetch_serpapi,
)
from app.persistence import create_pool


def provider_jobs(records: list[dict], city: str | None = None) -> tuple[list[JobInput], dict]:
    """Skip unusable external records explicitly; commit the validated remainder atomically."""
    jobs, reasons = [], {}
    for record in records:
        record = dict(record, salary=str(record.get("salary") or "Not specified"))
        if city:
            record["city"] = city
        try:
            jobs.append(JobInput.model_validate(record))
        except ValidationError as exc:
            for field in {str(error["loc"][0]) for error in exc.errors()}:
                reasons[field] = reasons.get(field, 0) + 1
    return jobs, {"received": len(records), "skipped": len(records) - len(jobs), "skipped_reasons": reasons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", type=Path, help="JSON array of JobInput records")
    source.add_argument("--keywords", nargs="+", help="Fetch configured external providers")
    parser.add_argument("--location", default="India")
    parser.add_argument("--city", help="Canonical city for all provider results (otherwise use provider location)")
    args = parser.parse_args()
    if args.file:
        records = json.loads(args.file.read_text(encoding="utf-8"))
        # User-authored imports fail as a whole on invalid input, before any writes.
        jobs = [JobInput.model_validate(record) for record in records]
        report = {"received": len(records), "skipped": 0, "skipped_reasons": {}}
    else:
        sources = []
        if ADZUNA_APP_ID and ADZUNA_APP_KEY:
            sources.append(fetch_adzuna(args.keywords, args.location))
        if JOOBLE_KEY:
            sources.append(fetch_jooble(args.keywords, args.location))
        if SERPAPI_KEY:
            sources.append(fetch_serpapi(args.keywords, args.location))
        if not sources:
            parser.error("No configured providers returned results; no mock listings are imported")
        records = [record for source in sources for record in source]
        jobs, report = provider_jobs(records, args.city)
    with create_pool() as pool:
        print(json.dumps(report | {"upserted": JobRepository(pool).upsert(jobs)}))


if __name__ == "__main__":
    main()

"""Import a JSON catalog or configured provider results, outside the read path."""

import argparse
import json
from pathlib import Path

from app.job_catalog import JobInput, JobRepository
from app.job_search import (
    ADZUNA_APP_ID,
    ADZUNA_APP_KEY,
    JOOBLE_KEY,
    SERPAPI_KEY,
    fetch_adzuna,
    fetch_jooble,
    fetch_serpapi,
    merge_results,
)
from app.persistence import create_pool


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
        records = merge_results(*sources)
        for record in records:
            record["salary"] = str(record.get("salary") or "Not specified")
            if args.city:
                record["city"] = args.city
    # Validate the whole import before its single transaction; failures leave no partial catalog.
    jobs = [JobInput.model_validate(record) for record in records]
    with create_pool() as pool:
        print({"upserted": JobRepository(pool).upsert(jobs)})


if __name__ == "__main__":
    main()

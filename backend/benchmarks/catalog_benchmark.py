"""Reproducible PostgreSQL + HTTP benchmark; no sleeps, planner overrides, or synthetic latencies."""

import argparse
import hashlib
import json
import math
import os
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import psycopg
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

from app.job_catalog import SearchRequest, search_query
from app.persistence import create_pool, database_url

HERE = Path(__file__).resolve().parent
CASES = {
    "driver_bengaluru": {"profile": {"role": "Driver", "location": "Bengaluru"}, "limit": 50},
    "plumber_pune": {"profile": {"role": "Plumber", "location": "Pune"}, "limit": 50},
    "electrician_india": {"profile": {"role": "Electrician", "location": "India"}, "limit": 50},
}


def stats(samples):
    return {
        "median_ms": statistics.median(samples),
        "p95_ms": sorted(samples)[math.ceil(len(samples) * 0.95) - 1],
        "min_ms": min(samples), "max_ms": max(samples), "samples_ms": samples,
    }


def snapshot(conn):
    return conn.execute("""SELECT count(*) AS rows, sum(id)::text AS id_sum,
        sum(hashtextextended(to_jsonb(jobs)::text, 0)::numeric)::text AS content_checksum
        FROM jobs""").fetchone()


def environment(conn):
    settings = conn.execute("""SELECT name, setting, unit FROM pg_settings WHERE name IN (
        'shared_buffers','work_mem','maintenance_work_mem','effective_cache_size',
        'max_parallel_workers_per_gather','max_connections','random_page_cost','seq_page_cost',
        'enable_seqscan','enable_indexscan','enable_bitmapscan','jit','fsync',
        'synchronous_commit','full_page_writes','default_statistics_target') ORDER BY name""").fetchall()
    cpu = next((line.split(':', 1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines()
                if line.startswith('model name')), platform.processor())
    memory = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    return {
        "postgresql": conn.execute("SELECT version() AS version").fetchone()["version"],
        "platform": platform.platform(), "python": platform.python_version(),
        "cpu": cpu, "logical_cpus": os.cpu_count(),
        "memory_total": memory["MemTotal"].strip(), "memory_available": memory["MemAvailable"].strip(),
        "settings": settings,
        "heap_bytes": conn.execute("SELECT pg_relation_size('jobs') AS bytes").fetchone()["bytes"],
        "index_bytes": conn.execute("SELECT pg_indexes_size('jobs') AS bytes").fetchone()["bytes"],
        "indexes": conn.execute("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'jobs' ORDER BY indexname").fetchall(),
        "migrations": conn.execute("SELECT version, name, checksum FROM schema_migrations ORDER BY version").fetchall(),
    }


def measure(args, url):
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    result = {
        "phase": args.phase, "started_at": datetime.now(timezone.utc).isoformat(),
        "warmups": args.warmups, "repetitions": args.repetitions, "concurrency": 1,
        "http_base_url": args.base_url, "cache_policy": "warm, no cache eviction; identical warmups for both phases",
        "seed_sha256": hashlib.sha256((HERE / "seed.sql").read_bytes()).hexdigest(),
        "cases": {},
    }
    with create_pool(url) as pool, pool.connection() as conn, httpx.Client(base_url=args.base_url, timeout=30) as client:
        result["environment"] = environment(conn)
        result["dataset"] = snapshot(conn)
        indexes = {item["indexname"] for item in result["environment"]["indexes"]}
        if args.phase == "before" and indexes != {"jobs_pkey", "jobs_identity_key_key"}:
            raise RuntimeError("Baseline must have only primary-key and identity integrity indexes")
        client.get("/health").raise_for_status()
        for name, payload in CASES.items():
            query, params, _ = search_query(SearchRequest(**payload))
            direct_ids = [row["id"] for row in conn.execute(query, params).fetchall()][:payload["limit"]]
            expected = client.post("/search_jobs", json=payload)
            expected.raise_for_status()
            expected_json = expected.json()
            if direct_ids != [row["id"] for row in expected_json["jobs"]]:
                raise RuntimeError("HTTP and direct SQL do not read the same catalog")
            for _ in range(args.warmups):
                conn.execute(query, params).fetchall()
                client.post("/search_jobs", json=payload).raise_for_status()
            sql_samples, http_samples = [], []
            # Interleave the same read paths in each phase; HTTP includes JSON parsing.
            for _ in range(args.repetitions):
                start = time.perf_counter_ns()
                conn.execute(query, params).fetchall()
                sql_samples.append((time.perf_counter_ns() - start) / 1_000_000)
                start = time.perf_counter_ns()
                response = client.post("/search_jobs", json=payload)
                response.raise_for_status()
                data = response.json()
                http_samples.append((time.perf_counter_ns() - start) / 1_000_000)
                if data != expected_json:
                    raise RuntimeError("Search result changed during benchmark")
            explain = conn.execute("EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON) " + query, params).fetchone()["QUERY PLAN"]
            text_plan = conn.execute("EXPLAIN (ANALYZE, BUFFERS, SETTINGS) " + query, params).fetchall()
            (output / f"{args.phase}-{name}.plan.json").write_text(json.dumps(explain, indent=2) + "\n")
            (output / f"{args.phase}-{name}.plan.txt").write_text("\n".join(row["QUERY PLAN"] for row in text_plan) + "\n")
            result["cases"][name] = {
                "request": payload, "query": query, "parameters": params,
                "result_sha256": hashlib.sha256(json.dumps(expected_json, sort_keys=True).encode()).hexdigest(),
                "result_count": expected_json["count"], "sql": stats(sql_samples), "http": stats(http_samples),
            }
            print(name, {key: {k: v for k, v in result["cases"][name][key].items() if k != "samples_ms"} for key in ("sql", "http")}, flush=True)
        if snapshot(conn) != result["dataset"]:
            raise RuntimeError("Dataset changed during benchmark")
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    (output / f"{args.phase}.json").write_text(json.dumps(result, indent=2) + "\n")


def compare(args):
    before = json.loads((args.output / "before.json").read_text())
    after = json.loads((args.output / "after.json").read_text())
    for key in ("dataset", "seed_sha256", "warmups", "repetitions", "concurrency", "http_base_url", "cache_policy"):
        if before[key] != after[key]:
            raise RuntimeError(f"Benchmark conditions differ: {key}")
    for key in ("postgresql", "cpu", "logical_cpus", "memory_total", "settings", "heap_bytes", "python"):
        if before["environment"][key] != after["environment"][key]:
            raise RuntimeError(f"Environment differs: {key}")
    lines = ["# JobSathi PostgreSQL search measurements", "", f"Generated: {after['finished_at']}", "",
             "| Query | Path | Before median / p95 (ms) | After median / p95 (ms) | Median speedup |",
             "|---|---|---:|---:|---:|"]
    for name, baseline in before["cases"].items():
        indexed = after["cases"][name]
        for key in ("request", "query", "parameters", "result_sha256", "result_count"):
            if baseline[key] != indexed[key]:
                raise RuntimeError(f"Query or result differs: {name}.{key}")
        for path in ("sql", "http"):
            old, new = baseline[path], indexed[path]
            lines.append(f"| {name} | {path} | {old['median_ms']:.3f} / {old['p95_ms']:.3f} | "
                         f"{new['median_ms']:.3f} / {new['p95_ms']:.3f} | {old['median_ms']/new['median_ms']:.2f}× |")
    lines.extend(["", "All dataset fingerprints, query SQL/parameters, returned-page hashes, PostgreSQL settings,",
                  "sample counts and cache policies matched. Raw individual samples and hardware metadata are in before.json / after.json.",
                  "p95 uses the nearest-rank definition. HTTP is real loopback TCP to Uvicorn, including routing, pooling,",
                  "query execution, scoring, serialization, response transfer and client JSON decoding.", ""])
    (args.output / "comparison.md").write_text("\n".join(lines))
    print("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["seed", "measure", "compare"])
    parser.add_argument("--rows", type=int, default=300000)
    parser.add_argument("--phase", choices=["before", "after"], default="before")
    parser.add_argument("--base-url", default="http://127.0.0.1:8011")
    parser.add_argument("--warmups", type=int, default=10)
    parser.add_argument("--repetitions", type=int, default=100)
    parser.add_argument("--output", type=Path, default=HERE / "results")
    args = parser.parse_args()
    if args.action == "compare":
        compare(args)
        return
    url = database_url()
    if not conninfo_to_dict(url).get("dbname", "").endswith("_benchmark"):
        parser.error("Use a dedicated database ending in _benchmark")
    if args.action == "seed":
        with psycopg.connect(url, row_factory=dict_row, autocommit=True) as conn:
            if conn.execute("SELECT count(*) AS count FROM jobs").fetchone()["count"]:
                parser.error("Seed requires an empty jobs table; never modifies existing catalog data")
            conn.execute((HERE / "seed.sql").read_text(), {"rows": args.rows})
            conn.execute("VACUUM (ANALYZE) jobs")
            print(snapshot(conn))
    else:
        if args.warmups < 1 or args.repetitions < 20:
            parser.error("Use at least one warmup and twenty measured repetitions")
        measure(args, url)


if __name__ == "__main__":
    main()

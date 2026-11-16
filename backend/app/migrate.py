"""Versioned, checksummed PostgreSQL migrations: python -m app.migrate."""

import argparse
import hashlib
from pathlib import Path

import psycopg

from app.persistence import database_url

MIGRATIONS = Path(__file__).with_name("migrations")


def migrate(url: str, target: int | None = None) -> list[str]:
    applied = []
    with psycopg.connect(url) as conn:
        # Serialize migration runners, including the first schema bootstrap.
        conn.execute("SELECT pg_advisory_xact_lock(18437, 1)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version integer PRIMARY KEY,
                name text NOT NULL,
                checksum text NOT NULL,
                applied_at timestamptz NOT NULL DEFAULT now()
            )
        """)
        existing = dict(conn.execute("SELECT version, checksum FROM schema_migrations"))
        for path in sorted(MIGRATIONS.glob("*.sql")):
            version = int(path.name.split("_", 1)[0])
            sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode()).hexdigest()
            if version in existing:
                if existing[version] != checksum:
                    raise RuntimeError(f"Migration checksum mismatch: {path.name}")
                continue
            if target is not None and version > target:
                continue
            conn.execute(sql)
            conn.execute(
                "INSERT INTO schema_migrations (version, name, checksum) VALUES (%s, %s, %s)",
                (version, path.name, checksum),
            )
            applied.append(path.name)
    return applied


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=int, help="Apply only versions up to this number")
    args = parser.parse_args()
    print({"applied": migrate(database_url(), args.target)})


if __name__ == "__main__":
    main()

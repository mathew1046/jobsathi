"""Bounded connection pooling and durable, atomic interview-session storage."""

import os
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import Depends, Request
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool


def database_url() -> str:
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required; run python -m app.migrate before starting the API")
    return url


def create_pool(url: str | None = None) -> ConnectionPool:
    return ConnectionPool(
        url or database_url(),
        min_size=1,
        max_size=int(os.getenv("DATABASE_POOL_SIZE", "4")),
        timeout=5,
        max_waiting=32,
        kwargs={
            "row_factory": dict_row,
            "connect_timeout": 5,
            "options": "-c statement_timeout=10000 -c idle_in_transaction_session_timeout=10000",
            # Avoid changing to a generic prepared plan after the fifth request.
            # Every search is planned for its actual optional filters, in both benchmarks.
            "prepare_threshold": None,
        },
        open=False,
    )


def get_pool(request: Request) -> ConnectionPool:
    return request.app.state.pool


PoolDep = Annotated[ConnectionPool, Depends(get_pool)]


def session_uuid(value) -> UUID | None:
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


class SessionRepository:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def create(self) -> str:
        session_id = uuid4()
        metadata = {"created_at": datetime.now(timezone.utc).isoformat(), "completed": False}
        with self.pool.connection() as conn:
            conn.execute("INSERT INTO sessions (id, metadata) VALUES (%s, %s)", (session_id, Jsonb(metadata)))
        return str(session_id)

    def get(self, session_id: str) -> dict | None:
        key = session_uuid(session_id)
        if key is None:
            return None
        with self.pool.connection() as conn:
            return conn.execute(
                "SELECT responses, metadata, profile, pdf_filename FROM sessions WHERE id = %s", (key,)
            ).fetchone()

    def append_response(self, session_id: str, response: dict) -> bool:
        with self.pool.connection() as conn:
            cursor = conn.execute(
                """UPDATE sessions SET responses = responses || %s::jsonb, updated_at = now()
                   WHERE id = %s AND profile IS NULL""",
                (Jsonb([response]), session_uuid(session_id)),
            )
            return cursor.rowcount == 1

    def complete(self, session_id: str, profile: dict, pdf_filename: str) -> None:
        metadata = {"completed": True, "completed_at": datetime.now(timezone.utc).isoformat()}
        with self.pool.connection() as conn:
            conn.execute(
                """UPDATE sessions SET profile = %s, pdf_filename = %s,
                   metadata = metadata || %s::jsonb, updated_at = now() WHERE id = %s""",
                (Jsonb(profile), pdf_filename, Jsonb(metadata), session_uuid(session_id)),
            )

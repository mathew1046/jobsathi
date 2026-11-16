import os

import pytest
from psycopg.conninfo import conninfo_to_dict

from app.migrate import migrate
from app.persistence import create_pool


@pytest.fixture(scope="session")
def database_url():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is required for real PostgreSQL integration tests")
    if not conninfo_to_dict(url).get("dbname", "").endswith("_test"):
        raise RuntimeError("Integration tests require a dedicated database ending in _test")
    migrate(url)
    return url


@pytest.fixture
def pool(database_url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", database_url)
    with create_pool(database_url) as pool:
        with pool.connection() as conn:
            conn.execute("TRUNCATE jobs, sessions RESTART IDENTITY")
        yield pool

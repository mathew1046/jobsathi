from pathlib import Path

import pytest
import yaml
from psycopg.conninfo import conninfo_to_dict

from app.persistence import database_url


@pytest.mark.parametrize("password", ["strong/password", "p@ss:#?%&=+ \\\'\"$[]"])
def test_compose_credentials_round_trip_through_libpq(monkeypatch, password):
    compose = yaml.safe_load((Path(__file__).parents[2] / "docker-compose.yml").read_text())
    for service in ("migrate", "backend"):
        environment = compose["services"][service]["environment"]
        assert environment["DATABASE_URL"] == ""
        assert environment["PGPASSWORD"] == "${POSTGRES_PASSWORD:-jobsathi}"
        for name, value in environment.items():
            monkeypatch.setenv(name, password if name == "PGPASSWORD" else value)
        parsed = conninfo_to_dict(database_url())
        assert parsed["password"] == password
        assert parsed["host"] == "postgres" and parsed["port"] == "5432"
        assert parsed["dbname"] == "jobsathi" and parsed["user"] == "jobsathi"


def test_database_url_takes_precedence_over_separate_credentials(monkeypatch):
    url = "postgresql://postgres@127.0.0.1:55432/jobsathi_test"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("PGDATABASE", "different")
    assert database_url() == url

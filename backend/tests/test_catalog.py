from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.job_catalog import JobInput, JobRepository, SearchRequest
from app.main import app
from app.migrate import migrate
from app.persistence import SessionRepository


def job(**overrides):
    data = {
        "title": "Delivery Driver", "company": "Example Logistics", "location": "Bengaluru",
        "source": "test", "url": "https://example.com/job/1", "description": "Valid licence required",
        "posted_at": datetime(2026, 11, 1, tzinfo=timezone.utc),
    }
    return JobInput(**(data | overrides))


def test_search_filters_and_frontend_contract(pool, monkeypatch):
    repository = JobRepository(pool)
    repository.upsert([
        job(), job(company="Other city", location="Delhi"),
        job(company="Closed", is_active=False), job(company="Foreign", country_code="US"),
        job(company="Unrelated", title="Plumber", description="Repair water pipes"),
    ])
    # Even when provider functions are unavailable, the real API searches its persistent catalog.
    def fail(*args, **kwargs):
        raise AssertionError("network provider called on catalog read")
    monkeypatch.setattr("requests.get", fail)
    monkeypatch.setattr("requests.post", fail)
    with TestClient(app) as client:
        response = client.post("/search_jobs", json={"profile": {"role": "Driver", "location": "  BENGALURU "}})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success" and data["count"] == 1
        assert data["jobs"][0]["company"] == "Example Logistics"
        assert {"title", "company", "location", "source", "salary", "url", "description", "relevance_score"} <= data["jobs"][0].keys()
        assert client.get("/health").json()["database"] == "postgresql"


def test_pagination_with_equal_timestamps_and_new_inserts(pool):
    repository = JobRepository(pool)
    repository.upsert([job(company=f"Employer {i}") for i in range(13)])
    request = SearchRequest(profile={"role": "driver", "location": "Bengaluru"}, limit=5)
    first = repository.search(request)
    ids = [row.id for row in first.jobs]
    repository.upsert([job(company="New employer", posted_at=datetime.now(timezone.utc))])
    cursor = first.next_cursor
    while cursor:
        page = repository.search(request.model_copy(update={"cursor": cursor}))
        ids.extend(row.id for row in page.jobs)
        cursor = page.next_cursor
    assert len(ids) == len(set(ids)) == 13
    assert ids == sorted(ids, reverse=True)


@pytest.mark.parametrize("payload,status", [
    ({"profile": {}}, 400),
    ({"profile": {"role": "Driver"}, "limit": 101}, 422),
    ({"profile": {"role": "Driver"}, "limit": 0}, 422),
    ({"profile": {"location": ["Bengaluru"]}}, 422),
    ({"profile": {"role": "Driver"}, "cursor": "broken-cursor"}, 422),
    ({"profile": {"role": "Driver"}, "country_code": "IND"}, 422),
])
def test_validation(pool, payload, status):
    with TestClient(app) as client:
        assert client.post("/search_jobs", json=payload).status_code == status


def test_cursor_bound_to_search_and_query_is_parameterized(pool):
    repository = JobRepository(pool)
    repository.upsert([job(company=f"Employer {i}") for i in range(3)])
    first = repository.search(SearchRequest(profile={"role": "Driver"}, limit=1))
    with pytest.raises(ValueError, match="Invalid cursor"):
        repository.search(SearchRequest(profile={"role": "Plumber"}, cursor=first.next_cursor))
    result = repository.search(SearchRequest(profile={"role": "'; DROP TABLE jobs; --"}))
    assert result.count == 0
    assert repository.search(SearchRequest(profile={"role": "Driver"})).count == 3


def test_upsert_is_deduplicated_updates_search_vector_and_is_atomic(pool):
    repository = JobRepository(pool)
    repository.upsert([job()])
    repository.upsert([job(source="second provider", description="Kannada spoken here", salary="24000/month")])
    result = repository.search(SearchRequest(profile={"skills": ["Kannada"]}))
    assert result.count == 1 and result.jobs[0].salary == "24000/month"
    invalid = job(company="Bad record").model_copy(update={"country_code": "INVALID"})
    with pytest.raises(psycopg.errors.CheckViolation):
        repository.upsert([job(company="Rolled back employer"), invalid])
    assert repository.search(SearchRequest(profile={"role": "Driver"})).count == 1


def test_missing_keyword_and_unicode_search_return_truthful_results(pool):
    repository = JobRepository(pool)
    repository.upsert([job(title="चालक", location="पुणे")])
    assert repository.search(SearchRequest(profile={"role": "चालक", "location": "पुणे"})).count == 1
    assert repository.search(SearchRequest(profile={"role": "Astronaut"})).count == 0
    assert repository.search(SearchRequest(profile={"location": "India"})).count == 1


def test_sessions_survive_restart_and_concurrent_appends(pool):
    with TestClient(app) as client:
        session_id = client.post("/start_session").json()["session_id"]
    repository = SessionRepository(pool)
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda i: repository.append_response(session_id, {"question_id": i}), range(24)))
    assert all(results)
    with TestClient(app):
        stored = repository.get(session_id)
        assert len(stored["responses"]) == 24
        assert {row["question_id"] for row in stored["responses"]} == set(range(24))
    repository.complete(session_id, {"name": "Arun"}, "resume.pdf")
    assert not repository.append_response(session_id, {"question_id": 25})
    assert repository.get(session_id)["profile"] == {"name": "Arun"}


def test_resume_flow_uses_database_after_restart(pool, monkeypatch, tmp_path):
    import app.main as main

    monkeypatch.setattr(main, "DATABASE_DIR", str(tmp_path))
    async def extract(*args, **kwargs):
        return {"translation": "Arun", "extracted_data": {"name": "Arun"}}
    monkeypatch.setattr(main, "call_gemini", extract)
    with TestClient(app) as client:
        session_id = client.post("/start_session").json()["session_id"]
        result = client.post("/ask_llm", json={"session_id": session_id, "transcript": "Arun", "field": "name"})
        assert result.status_code == 200
    async def profile(*args, **kwargs):
        return {"name": "Arun", "role": "Driver"}
    monkeypatch.setattr(main, "call_gemini", profile)
    with TestClient(app) as client:
        result = client.post("/build_profile", json={"session_id": session_id})
        assert result.status_code == 200
        filename = result.json()["pdf_filename"]
        assert client.get(f"/download_resume/{filename}").content.startswith(b"%PDF")
        assert client.post("/build_profile", json={"session_id": session_id}).json() == result.json()
        assert client.post("/ask_llm", json={"session_id": session_id, "transcript": "x"}).status_code == 409
        assert client.post("/build_profile", json={"session_id": "invalid"}).status_code == 400


def test_failed_profile_persistence_returns_sanitized_unavailable(pool, monkeypatch, tmp_path):
    import app.main as main

    monkeypatch.setattr(main, "DATABASE_DIR", str(tmp_path))
    async def profile(*args, **kwargs):
        return {"name": "Arun", "role": "Driver"}
    def unavailable(*args, **kwargs):
        raise psycopg.OperationalError("connection failed with private connection details")
    monkeypatch.setattr(main, "call_gemini", profile)
    monkeypatch.setattr(SessionRepository, "complete", unavailable)
    repository = SessionRepository(pool)
    session_id = repository.create()
    repository.append_response(session_id, {"translated_text": "Arun Driver", "extracted_data": {"name": "Arun"}})
    with TestClient(app) as client:
        response = client.post("/build_profile", json={"session_id": session_id})
    assert response.status_code == 503
    assert response.json() == {"detail": "Database temporarily unavailable"}
    assert repository.get(session_id)["profile"] is None


def test_migrations_are_idempotent_and_checksummed(pool, database_url, tmp_path, monkeypatch):
    from app import migrate as migration_module

    assert migrate(database_url) == []
    original = migration_module.MIGRATIONS / "001_persistence.sql"
    (tmp_path / original.name).write_text(original.read_text() + "\n-- changed", encoding="utf-8")
    monkeypatch.setattr(migration_module, "MIGRATIONS", tmp_path)
    with pytest.raises(RuntimeError, match="Migration checksum mismatch"):
        migrate(database_url)

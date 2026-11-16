import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

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


def test_generated_frontend_profile_matches_supplied_demo(pool):
    records = json.loads((Path(__file__).parents[1] / "examples" / "jobs.json").read_text())
    JobRepository(pool).upsert([JobInput.model_validate(record) for record in records])
    profile = {
        "name": "Arun Kumar", "role": "Professional Driver", "location": "Bengaluru, Karnataka",
        "skills": ["Two Wheeler Driving", "Customer Communication"], "experience_years": 3,
        "experience_details": [{"role": "Delivery Driver", "company": "Acme Logistics"}],
        "education": [{"degree": "Secondary School"}], "certifications": ["Driving Licence"],
        "languages": ["Kannada", "Hindi"],
    }
    with TestClient(app) as client:
        result = client.post("/search_jobs", json={"profile": profile})
        assert result.status_code == 200
        data = result.json()
        assert data["count"] == 1
        assert data["jobs"][0]["title"] == "Delivery Driver"
        assert data["jobs"][0]["location"] == "Bengaluru, Karnataka"
        assert data["jobs"][0]["relevance_score"] >= 15
        alias = client.post("/search_jobs", json={"profile": profile | {"location": "Bangalore, Karnataka, India"}}).json()
        assert alias == data


def test_city_normalization_is_shared_by_import_and_search(pool):
    repository = JobRepository(pool)
    repository.upsert([job(location="Bangalore, Karnataka, India")])
    repository.upsert([job(location="Bengaluru, Karnataka", source="another provider")])
    for location in ("Bengaluru", "Bengaluru, Karnataka", "  BANGALORE , Karnataka, India "):
        result = repository.search(SearchRequest(profile={"role": "Professional Driver", "location": location}))
        assert result.count == 1
        assert result.jobs[0].location == "Bengaluru, Karnataka"
    with pool.connection() as conn:
        assert conn.execute("SELECT city_key FROM jobs").fetchall() == [{"city_key": "bengaluru"}]


def test_role_eligibility_precedes_limit_and_ignores_previous_employer(pool):
    repository = JobRepository(pool)
    repository.upsert([
        job(company=f"Warehouse {i}", title="Warehouse Helper", location="Delhi",
            description="Acme inventory and loading work", posted_at=datetime(2026, 11, 2, tzinfo=timezone.utc))
        for i in range(60)
    ] + [job(company="Relevant employer", location="Delhi", description="Driver with a licence")])
    profile = {"role": "Professional Driver", "experience_details": [{"company": "Acme"}],
               "skills": ["inventory"], "location": "India"}
    with TestClient(app) as client:
        data = client.post("/search_jobs", json={"profile": profile}).json()
    assert data["count"] == 1 and data["next_cursor"] is None
    assert data["jobs"][0]["company"] == "Relevant employer"
    assert data["jobs"][0]["relevance_score"] >= 15


def test_text_eligibility_and_score_agree_without_substring_match(pool):
    repository = JobRepository(pool)
    repository.upsert([job(title="Driver of heavy vehicles", description="Vehicle inspections")])
    # Terms can occur across title and description; literal phrase scoring used to give zero.
    result = repository.search(SearchRequest(profile={"role": "Professional heavy vehicle driver"}))
    assert result.count == 1 and result.jobs[0].relevance_score >= 7


def test_role_and_structured_skill_fallbacks(pool):
    repository = JobRepository(pool)
    repository.upsert([job(), job(company="Pipes", title="Plumber", description="Pipe installation")])
    experience = repository.search(SearchRequest(profile={"experience_details": [{"role": "Professional Driver", "company": "Pipes"}]}))
    assert experience.count == 1 and experience.jobs[0].title == "Delivery Driver"
    skills = repository.search(SearchRequest(profile={"skills": [{"name": "Pipe installation"}]}))
    assert skills.count == 1 and skills.jobs[0].relevance_score >= 4


def test_mixed_provider_import_skips_invalid_records_with_counts(pool, monkeypatch, capsys):
    from app import import_jobs

    record = job(location="Bengaluru, Karnataka").model_dump(mode="json")
    monkeypatch.setattr(import_jobs, "ADZUNA_APP_ID", "configured")
    monkeypatch.setattr(import_jobs, "ADZUNA_APP_KEY", "configured")
    monkeypatch.setattr(import_jobs, "JOOBLE_KEY", "")
    monkeypatch.setattr(import_jobs, "SERPAPI_KEY", "")
    monkeypatch.setattr(import_jobs, "fetch_adzuna", lambda *args: [
        record, record | {"company": "Missing application options", "url": ""},
        record | {"company": "Broken listing", "title": "", "url": "https://"},
    ])
    monkeypatch.setattr("sys.argv", ["import_jobs", "--keywords", "Driver"])
    import_jobs.main()
    assert json.loads(capsys.readouterr().out) == {
        "received": 3, "upserted": 1, "skipped": 2, "skipped_reasons": {"url": 2, "title": 1},
    }
    result = JobRepository(pool).search(SearchRequest(profile={"role": "Driver", "location": "Bengaluru"}))
    assert result.count == 1 and result.jobs[0].company == "Example Logistics"


def test_invalid_local_import_rejects_entire_batch(pool, monkeypatch, tmp_path):
    from app import import_jobs

    record = job().model_dump(mode="json")
    source = tmp_path / "jobs.json"
    source.write_text(json.dumps([record, record | {"company": "Invalid", "url": ""}]))
    monkeypatch.setattr("sys.argv", ["import_jobs", "--file", str(source)])
    with pytest.raises(ValidationError):
        import_jobs.main()
    assert JobRepository(pool).search(SearchRequest(profile={"role": "Driver"})).count == 0


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

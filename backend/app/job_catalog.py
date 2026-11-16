"""PostgreSQL job ingestion and bounded, parameterized catalog search."""

import base64
import hashlib
import json
import unicodedata
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, Field, field_validator

from app.job_search import generate_keywords, score_relevance
from app.persistence import PoolDep

router = APIRouter(tags=["jobs"])


def normalize_location(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


class JobInput(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    company: str = Field(min_length=1, max_length=500)
    location: str = Field(min_length=1, max_length=500)
    city: str | None = Field(default=None, max_length=200)
    country_code: str = Field(default="IN", pattern=r"^[A-Z]{2}$")
    source: str = Field(min_length=1, max_length=100)
    url: str = Field(max_length=4000, pattern=r"^https?://")
    description: str = Field(default="", max_length=20000)
    salary: str = Field(default="Not specified", max_length=200)
    is_active: bool = True
    posted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("title", "company", "location", "source", "city")
    @classmethod
    def nonblank(cls, value):
        if value is not None and not value.strip():
            raise ValueError("must not be blank")
        return value.strip() if value is not None else None

    @field_validator("posted_at")
    @classmethod
    def aware_timestamp(cls, value):
        if value.tzinfo is None:
            raise ValueError("posted_at must include a timezone")
        return value


class SearchRequest(BaseModel):
    profile: dict[str, Any]
    country_code: str = Field(default="IN", pattern=r"^[A-Z]{2}$")
    limit: int = Field(default=50, ge=1, le=100)
    cursor: str | None = Field(default=None, max_length=1000)

    @field_validator("profile")
    @classmethod
    def valid_profile(cls, value):
        if len(json.dumps(value)) > 16000:
            raise ValueError("profile is too large")
        for key in ("role", "location"):
            if value.get(key) is not None and not isinstance(value[key], str):
                raise ValueError(f"{key} must be a string or null")
        return value


class JobResult(BaseModel):
    id: int
    title: str
    company: str
    location: str
    source: str
    url: str
    description: str
    salary: str
    posted_at: datetime
    relevance_score: int


class SearchResponse(BaseModel):
    status: Literal["success"] = "success"
    jobs: list[JobResult]
    count: int
    next_cursor: str | None = None


def search_query(request: SearchRequest) -> tuple[str, list, str]:
    """One shared query for the API, tests, benchmarks, and EXPLAIN capture."""
    keywords = generate_keywords(request.profile)
    city = normalize_location(request.profile.get("location") or "")
    if city in {"india", "null", "none", "n/a"}:
        city = ""
    fingerprint = hashlib.sha256(json.dumps([request.country_code, city, keywords]).encode()).hexdigest()[:16]
    clauses = ["is_active", "country_code = %s"]
    params: list = [request.country_code]
    if city:
        clauses.append("city_key = %s")
        params.append(city)
    if keywords:
        terms = " || ".join("plainto_tsquery('simple', %s)" for _ in keywords)
        clauses.append(f"search_document @@ ({terms})")
        params.extend(keywords)
    if request.cursor:
        try:
            stamp, job_id, previous = json.loads(base64.urlsafe_b64decode(request.cursor.encode()))
            stamp = datetime.fromisoformat(stamp)
            if stamp.tzinfo is None or type(job_id) is not int or job_id < 1 or previous != fingerprint:
                raise ValueError
        except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("Invalid cursor for this search") from exc
        clauses.append("(posted_at, id) < (%s, %s)")
        params.extend([stamp, job_id])
    params.append(request.limit + 1)
    query = f"""SELECT id, title, company, location, source, url, description, salary, posted_at
                FROM jobs WHERE {' AND '.join(clauses)}
                ORDER BY posted_at DESC, id DESC LIMIT %s"""
    return query, params, fingerprint


class JobRepository:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def upsert(self, jobs: list[JobInput]) -> int:
        # The same title/company/location from different sources is one listing.
        # Refresh preserves its original posted_at unless an explicit source date is supplied.
        with self.pool.connection() as conn, conn.cursor() as cursor:
            for job in jobs:
                city_key = normalize_location(job.city or job.location)
                identity = hashlib.sha256(json.dumps([
                    normalize_location(job.title), normalize_location(job.company),
                    city_key, job.country_code,
                ]).encode()).hexdigest()
                cursor.execute(
                    """INSERT INTO jobs (identity_key, title, company, location, city_key, country_code,
                        source, url, description, salary, is_active, posted_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (identity_key) DO UPDATE SET
                         title = EXCLUDED.title, company = EXCLUDED.company, location = EXCLUDED.location,
                         source = EXCLUDED.source, url = EXCLUDED.url, description = EXCLUDED.description,
                         salary = EXCLUDED.salary, is_active = EXCLUDED.is_active, updated_at = now(),
                         posted_at = CASE WHEN %s THEN EXCLUDED.posted_at ELSE jobs.posted_at END""",
                    (identity, job.title, job.company, job.location, city_key, job.country_code,
                     job.source, job.url, job.description, job.salary, job.is_active, job.posted_at,
                     "posted_at" in job.model_fields_set),
                )
        return len(jobs)

    def search(self, request: SearchRequest) -> SearchResponse:
        query, params, fingerprint = search_query(request)
        with self.pool.connection() as conn:
            rows = conn.execute(query, params).fetchall()
        more = len(rows) > request.limit
        rows = rows[:request.limit]
        next_cursor = None
        if more:
            last = rows[-1]
            next_cursor = base64.urlsafe_b64encode(json.dumps([
                last["posted_at"].isoformat(), last["id"], fingerprint,
            ]).encode()).decode()
        jobs = [JobResult(**row, relevance_score=score_relevance(row, request.profile)) for row in rows]
        return SearchResponse(jobs=jobs, count=len(jobs), next_cursor=next_cursor)


@router.post("/search_jobs")
def search_jobs_endpoint(payload: SearchRequest, pool: PoolDep) -> SearchResponse:
    if not payload.profile:
        raise HTTPException(status_code=400, detail="Profile data is required")
    try:
        return JobRepository(pool).search(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

"""Tests the /jobs router's DELETE endpoint (clear all jobs/companies/contacts).

Uses httpx.AsyncClient over an ASGI transport with the get_session dependency
overridden to the test's in-memory db_session fixture — no lifespan events fire,
so this never touches the real dev database.
"""

import json

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db import get_session
from app.main import app
from app.models import Company, Contact, Job, JobStatus


@pytest.mark.asyncio
async def test_clear_jobs_deletes_jobs_companies_and_contacts(db_session):
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    try:
        job = Job(input_url="acme.com", normalized_domain="acme.com", status=JobStatus.DONE)
        db_session.add(job)
        await db_session.flush()
        company = Company(job_id=job.id, name="Acme", website="acme.com")
        db_session.add(company)
        await db_session.flush()
        db_session.add(
            Contact(
                company_id=company.id, first_name="Jane", last_name="Doe",
                title="CEO", source_stage="persist",
            )
        )
        await db_session.commit()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/jobs")

        assert response.status_code == 200
        body = response.json()
        assert body == {"deleted_jobs": 1, "deleted_companies": 1, "deleted_contacts": 1}

        assert (await db_session.execute(select(Job))).scalars().all() == []
        assert (await db_session.execute(select(Company))).scalars().all() == []
        assert (await db_session.execute(select(Contact))).scalars().all() == []
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_clear_jobs_on_empty_db_returns_zero_counts(db_session):
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/jobs")

        assert response.status_code == 200
        assert response.json() == {"deleted_jobs": 0, "deleted_companies": 0, "deleted_contacts": 0}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_submit_jobs_persists_target_titles_on_job(db_session, monkeypatch):
    async def override_get_session():
        yield db_session

    # Submitting for real would enqueue a background pipeline run against the
    # app's real (non-test) database/API clients — this test only cares about
    # what gets persisted on the Job row at submission time.
    monkeypatch.setattr("app.routers.jobs.job_queue.enqueue", lambda job_id: None)

    app.dependency_overrides[get_session] = override_get_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/jobs",
                json={
                    "urls_text": "acme.com",
                    "confirmed": False,
                    "target_titles": {
                        "executive": ["CEO"],
                        "departments": {"Sales": ["Director of Sales"]},
                    },
                },
            )

        assert response.status_code == 200

        job = (await db_session.execute(select(Job))).scalar_one()
        assert json.loads(job.target_titles) == {
            "executive": ["CEO"],
            "departments": {"Sales": ["Director of Sales"]},
        }
    finally:
        app.dependency_overrides.clear()

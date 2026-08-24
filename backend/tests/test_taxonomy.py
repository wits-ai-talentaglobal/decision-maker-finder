import json

import pytest

from app.models import Job, JobStatus, TitleTaxonomy
from app.taxonomy import (
    DEFAULT_TAXONOMY_SEED,
    get_active_titles,
    get_titles_for_job,
    seed_default_taxonomy,
)


def _job(target_titles: str | None) -> Job:
    return Job(
        input_url="acme.com",
        normalized_domain="acme.com",
        status=JobStatus.QUEUED,
        target_titles=target_titles,
    )


@pytest.mark.asyncio
async def test_seed_default_taxonomy_populates_table(db_session):
    await seed_default_taxonomy(db_session)
    titles = await get_active_titles(db_session)
    assert len(titles) == len(DEFAULT_TAXONOMY_SEED)
    assert "CEO" in titles


@pytest.mark.asyncio
async def test_seed_default_taxonomy_is_idempotent(db_session):
    await seed_default_taxonomy(db_session)
    await seed_default_taxonomy(db_session)
    titles = await get_active_titles(db_session)
    assert len(titles) == len(DEFAULT_TAXONOMY_SEED)


@pytest.mark.asyncio
async def test_inactive_titles_excluded(db_session):
    await seed_default_taxonomy(db_session)
    db_session.add(TitleTaxonomy(label="Receptionist", category="other", is_active=False))
    await db_session.commit()

    titles = await get_active_titles(db_session)
    assert "Receptionist" not in titles


@pytest.mark.asyncio
async def test_get_titles_for_job_returns_flattened_selection_when_present(db_session):
    target_titles = json.dumps(
        {"executive": ["CEO"], "departments": {"Sales": ["Director of Sales", "Sales Manager"]}}
    )
    titles = await get_titles_for_job(_job(target_titles), db_session)
    assert titles == ["CEO", "Director of Sales", "Sales Manager"]


@pytest.mark.asyncio
async def test_get_titles_for_job_falls_back_when_target_titles_absent(db_session):
    await seed_default_taxonomy(db_session)
    titles = await get_titles_for_job(_job(None), db_session)
    assert titles == await get_active_titles(db_session)


@pytest.mark.asyncio
async def test_get_titles_for_job_falls_back_when_selection_is_empty(db_session):
    await seed_default_taxonomy(db_session)
    target_titles = json.dumps({"executive": [], "departments": {"Sales": []}})
    titles = await get_titles_for_job(_job(target_titles), db_session)
    assert titles == await get_active_titles(db_session)


@pytest.mark.asyncio
async def test_get_titles_for_job_falls_back_on_malformed_json(db_session):
    await seed_default_taxonomy(db_session)
    titles = await get_titles_for_job(_job("not json"), db_session)
    assert titles == await get_active_titles(db_session)

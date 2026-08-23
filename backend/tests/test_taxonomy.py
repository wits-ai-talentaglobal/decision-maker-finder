import pytest

from app.models import TitleTaxonomy
from app.taxonomy import DEFAULT_TAXONOMY_SEED, get_active_titles, seed_default_taxonomy


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

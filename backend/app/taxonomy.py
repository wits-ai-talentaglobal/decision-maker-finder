from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TitleTaxonomy

# Default seed list: general-purpose leadership taxonomy (CEO/owner/founder/partner,
# CXO, directors, department heads). This is only a *seed* — the source of truth is
# the title_taxonomy DB table, which can be edited/extended per vertical without
# touching pipeline code.
DEFAULT_TAXONOMY_SEED: list[tuple[str, str]] = [
    # CEO / owner / founder / partner
    ("CEO", "ownership"),
    ("Chief Executive Officer", "ownership"),
    ("Owner", "ownership"),
    ("Co-Owner", "ownership"),
    ("Founder", "ownership"),
    ("Co-Founder", "ownership"),
    ("Partner", "ownership"),
    ("Managing Partner", "ownership"),
    ("President", "ownership"),
    # CXO
    ("CFO", "cxo"),
    ("Chief Financial Officer", "cxo"),
    ("COO", "cxo"),
    ("Chief Operating Officer", "cxo"),
    ("CTO", "cxo"),
    ("Chief Technology Officer", "cxo"),
    ("CMO", "cxo"),
    ("Chief Marketing Officer", "cxo"),
    ("CPO", "cxo"),
    ("Chief Product Officer", "cxo"),
    ("CRO", "cxo"),
    ("Chief Revenue Officer", "cxo"),
    ("CHRO", "cxo"),
    ("Chief Human Resources Officer", "cxo"),
    # Directors
    ("Director", "director"),
    ("Managing Director", "director"),
    ("Executive Director", "director"),
    ("Regional Director", "director"),
    ("Vice President", "director"),
    ("VP", "director"),
    # Department heads
    ("Head of Department", "department_head"),
    ("Department Head", "department_head"),
    ("Head of Sales", "department_head"),
    ("Head of Marketing", "department_head"),
    ("Head of Operations", "department_head"),
    ("Head of Product", "department_head"),
    ("Head of Engineering", "department_head"),
    ("Head of Finance", "department_head"),
    ("Head of HR", "department_head"),
    ("Head of Human Resources", "department_head"),
]


async def get_active_titles(session: AsyncSession) -> list[str]:
    result = await session.execute(
        select(TitleTaxonomy.label).where(TitleTaxonomy.is_active.is_(True))
    )
    return [row[0] for row in result.all()]


async def seed_default_taxonomy(session: AsyncSession) -> None:
    existing = await session.execute(select(TitleTaxonomy.label))
    existing_labels = {row[0] for row in existing.all()}

    for label, category in DEFAULT_TAXONOMY_SEED:
        if label not in existing_labels:
            session.add(TitleTaxonomy(label=label, category=category, is_active=True))

    await session.commit()

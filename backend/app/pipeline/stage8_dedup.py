"""Stage 8: Dedup — check for an existing Apollo ID or LinkedIn URL before inserting."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contact
from app.schemas import DedupInput, DedupResult


async def dedup_contacts(stage_input: DedupInput, session: AsyncSession) -> DedupResult:
    linkedin_urls = [c.linkedin_url for c in stage_input.contacts if c.linkedin_url]
    apollo_ids = [c.apollo_id for c in stage_input.contacts if c.apollo_id]

    existing_linkedin: set[str] = set()
    existing_apollo: set[str] = set()

    if linkedin_urls:
        result = await session.execute(
            select(Contact.linkedin_url).where(Contact.linkedin_url.in_(linkedin_urls))
        )
        existing_linkedin = {row[0] for row in result.all()}

    if apollo_ids:
        result = await session.execute(
            select(Contact.apollo_id).where(Contact.apollo_id.in_(apollo_ids))
        )
        existing_apollo = {row[0] for row in result.all()}

    new_contacts = []
    skipped = 0
    for contact in stage_input.contacts:
        is_duplicate = (contact.linkedin_url is not None and contact.linkedin_url in existing_linkedin) or (
            contact.apollo_id is not None and contact.apollo_id in existing_apollo
        )
        if is_duplicate:
            skipped += 1
        else:
            new_contacts.append(contact)

    return DedupResult(new_contacts=new_contacts, skipped_duplicates=skipped)

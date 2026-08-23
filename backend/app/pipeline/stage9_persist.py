"""Stage 9: Persist + Surface — write Contact rows, mark the Job done, broadcast over WS."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contact, Job, JobStatus
from app.schemas import NormalizedContact
from app.ws_manager import WebSocketManager


async def persist_contacts_and_complete(
    job: Job,
    company_id: int,
    new_contacts: list[NormalizedContact],
    source_stage: str,
    session: AsyncSession,
    ws_manager: WebSocketManager,
) -> None:
    for contact in new_contacts:
        session.add(
            Contact(
                company_id=company_id,
                first_name=contact.first_name,
                last_name=contact.last_name,
                title=contact.title,
                linkedin_url=contact.linkedin_url,
                apollo_id=contact.apollo_id,
                email=contact.email,
                email_status=contact.email_status,
                phone=contact.phone,
                source_stage=source_stage,
            )
        )

    job.status = JobStatus.DONE
    await session.commit()

    await ws_manager.broadcast(
        {
            "type": "job_update",
            "job_id": job.id,
            "status": job.status.value,
            "contact_count": len(new_contacts),
        }
    )

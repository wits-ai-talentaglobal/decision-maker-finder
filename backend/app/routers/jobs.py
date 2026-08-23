from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db import get_session
from app.models import Company, Contact, Job, JobStatus
from app.normalize import parse_url_list
from app.queue import job_queue
from app.schemas import BatchEstimate, ClearJobsResult, JobOut, JobSubmitRequest

router = APIRouter(prefix="/jobs", tags=["jobs"])

# Rough per-URL API-call estimate used for the >10-URL cost-control confirmation.
# Assumes up to ~5 decision-maker candidates per company for the per-candidate stages.
ASSUMED_CANDIDATES_PER_COMPANY = 5


def _estimate_calls(url_count: int) -> BatchEstimate:
    apify_calls = url_count  # Stage 2: one scrape per company
    llm_calls = url_count * (
        1  # Stage 1: Sonar identity resolution
        + 1  # Stage 3: batch decision-maker extraction
        + ASSUMED_CANDIDATES_PER_COMPANY  # Stage 4: one validation call per candidate
    )
    apollo_calls = url_count * ASSUMED_CANDIDATES_PER_COMPANY  # Stage 5
    hunter_calls = url_count * ASSUMED_CANDIDATES_PER_COMPANY  # Stage 6 (upper bound)

    return BatchEstimate(
        url_count=url_count,
        invalid_entries=[],
        estimated_apify_calls=apify_calls,
        estimated_llm_calls=llm_calls,
        estimated_apollo_calls=apollo_calls,
        estimated_hunter_calls=hunter_calls,
        requires_confirmation=url_count > settings.batch_confirmation_threshold,
    )


@router.post("", response_model=list[JobOut] | BatchEstimate)
async def submit_jobs(
    request: JobSubmitRequest, session: AsyncSession = Depends(get_session)
):
    valid_domains, invalid_entries = parse_url_list(request.urls_text)

    if not valid_domains:
        raise HTTPException(status_code=422, detail="no valid website URLs found in input")

    estimate = _estimate_calls(len(valid_domains))
    estimate.invalid_entries = invalid_entries

    if estimate.requires_confirmation and not request.confirmed:
        return estimate

    jobs: list[Job] = []
    for domain in valid_domains:
        job = Job(input_url=domain, normalized_domain=domain, status=JobStatus.QUEUED)
        session.add(job)
        jobs.append(job)

    await session.commit()

    for job in jobs:
        await session.refresh(job, attribute_names=["id", "created_at", "updated_at"])

    # Build responses before enqueueing: a freshly created job never has a Company yet,
    # and touching the lazy `company` relationship here would trigger an implicit async
    # lazy-load outside of any awaited context (SQLAlchemy MissingGreenlet error).
    responses = [
        JobOut(
            id=job.id,
            input_url=job.input_url,
            normalized_domain=job.normalized_domain,
            status=job.status,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            company=None,
        )
        for job in jobs
    ]

    for job in jobs:
        job_queue.enqueue(job.id)

    return responses


@router.get("", response_model=list[JobOut])
async def list_jobs(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Job)
        .options(selectinload(Job.company).selectinload(Company.contacts))
        .order_by(Job.created_at.desc())
    )
    jobs = result.scalars().all()
    return [JobOut.model_validate(job) for job in jobs]


@router.delete("", response_model=ClearJobsResult)
async def clear_jobs(session: AsyncSession = Depends(get_session)):
    """Delete every job, company, and contact. Does not cancel jobs already
    in flight — an in-progress job may re-insert its own row(s) after this runs."""
    deleted_contacts = (await session.execute(delete(Contact))).rowcount
    deleted_companies = (await session.execute(delete(Company))).rowcount
    deleted_jobs = (await session.execute(delete(Job))).rowcount
    await session.commit()

    return ClearJobsResult(
        deleted_jobs=deleted_jobs,
        deleted_companies=deleted_companies,
        deleted_contacts=deleted_contacts,
    )


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Job)
        .options(selectinload(Job.company).selectinload(Company.contacts))
        .where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return JobOut.model_validate(job)

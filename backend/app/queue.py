"""In-process async job queue: asyncio.Semaphore-gated concurrency limiter running
the pipeline per job, with per-stage retry and per-job failure isolation.

Each submitted job becomes one asyncio task. A failure at any stage marks that job
"failed" with the failing stage name and stops processing *that job only* — the
semaphore slot frees up and the next queued job proceeds unaffected.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import SessionLocal
from app.integrations.apify_client import ApifyEmployeeScraperClient
from app.integrations.apollo_client import ApolloEnrichmentClient
from app.integrations.claude_client import ClaudeClassifierClient
from app.integrations.hunter_client import HunterEmailClient
from app.integrations.openrouter_client import OpenRouterSonarClient
from app.models import Company, Job, JobStatus
from app.pipeline import STAGE_TO_JOB_STATUS, PipelineStage, StageFailure
from app.pipeline.stage1_identity import resolve_company_identity
from app.pipeline.stage2_employees import scrape_employees
from app.pipeline.stage3_identify import search_decision_makers_directly
from app.pipeline.stage4_validate import validate_candidates
from app.pipeline.stage5_enrich import enrich_contacts
from app.pipeline.stage6_email_fallback import apply_email_fallback
from app.pipeline.stage7_normalize import normalize_contacts
from app.pipeline.stage8_dedup import dedup_contacts
from app.pipeline.stage9_persist import persist_contacts_and_complete
from app.schemas import (
    AiSearchInput,
    ClassifyEmployeesInput,
    DecisionMakerCandidate,
    DedupInput,
    EmailFallbackInput,
    EmployeesInput,
    EnrichInput,
    IdentityInput,
)
from app.taxonomy import get_titles_for_job
from app.ws_manager import ws_manager

logger = logging.getLogger(__name__)

STAGE_MAX_RETRIES = 2
STAGE_RETRY_BACKOFF_SECONDS = 0.5

T = TypeVar("T")


class JobQueue:
    def __init__(self, concurrency_limit: int) -> None:
        self._semaphore = asyncio.Semaphore(concurrency_limit)

    def enqueue(self, job_id: int) -> None:
        asyncio.create_task(self._run_job(job_id))

    async def _run_job(self, job_id: int) -> None:
        async with self._semaphore, SessionLocal() as session:
            job = await session.get(Job, job_id)
            if job is None:
                logger.error("job %s not found, skipping", job_id)
                return
            try:
                await self._run_pipeline(job, session)
            except StageFailure as failure:
                await self._fail_job(job, session, failure.stage, str(failure))
            except Exception as exc:  # noqa: BLE001 - last-resort isolation for this job only
                await self._fail_job(
                    job, session, PipelineStage.RESOLVE_IDENTITY, f"unexpected error: {exc}"
                )

    async def _run_pipeline(self, job: Job, session: AsyncSession) -> None:
        active_titles = await get_titles_for_job(job, session)

        # --- Stage 1: Company Identity Resolution ---
        await self._set_status(job, session, PipelineStage.RESOLVE_IDENTITY)
        identity = await self._with_retry(
            PipelineStage.RESOLVE_IDENTITY,
            lambda: resolve_company_identity(
                IdentityInput(job_id=job.id, normalized_domain=job.normalized_domain),
                OpenRouterSonarClient(),
            ),
        )
        company = Company(
            job_id=job.id,
            name=identity.company_name,
            website=identity.website,
            linkedin_url=identity.linkedin_url,
            city=identity.city,
            state=identity.state,
            resolved_confidence=identity.resolved_confidence,
        )
        session.add(company)
        await session.flush()

        # --- Branch on whether Stage 1 resolved a LinkedIn company page ---
        await self._set_status(job, session, PipelineStage.IDENTIFY_DECISION_MAKERS)
        candidates: list[DecisionMakerCandidate]
        if identity.linkedin_url:
            # Path A: scrape employees, then classify each one individually.
            await self._set_status(job, session, PipelineStage.SCRAPE_EMPLOYEES)
            employees_result = await self._with_retry(
                PipelineStage.SCRAPE_EMPLOYEES,
                lambda: scrape_employees(
                    EmployeesInput(
                        job_id=job.id,
                        company_name=identity.company_name,
                        linkedin_url=identity.linkedin_url,
                    ),
                    ApifyEmployeeScraperClient(),
                ),
            )
            await self._set_status(job, session, PipelineStage.VALIDATE_CANDIDATES)
            classify_result = await self._with_retry(
                PipelineStage.VALIDATE_CANDIDATES,
                lambda: validate_candidates(
                    ClassifyEmployeesInput(
                        job_id=job.id,
                        employees=employees_result.employees,
                        active_titles=active_titles,
                    ),
                    ClaudeClassifierClient(),
                ),
            )
            candidates = classify_result.validated
        else:
            # Path B: no LinkedIn company page — search directly for candidates.
            search_result = await self._with_retry(
                PipelineStage.IDENTIFY_DECISION_MAKERS,
                lambda: search_decision_makers_directly(
                    AiSearchInput(
                        job_id=job.id,
                        company_name=identity.company_name,
                        domain=job.normalized_domain,
                        active_titles=active_titles,
                    ),
                    OpenRouterSonarClient(),
                ),
            )
            candidates = search_result.candidates

        # --- Stage 5: Contact Enrichment ---
        await self._set_status(job, session, PipelineStage.ENRICH_CONTACTS)
        enrich_result = await self._with_retry(
            PipelineStage.ENRICH_CONTACTS,
            lambda: enrich_contacts(
                EnrichInput(job_id=job.id, candidates=candidates, domain=job.normalized_domain),
                ApolloEnrichmentClient(),
            ),
        )

        # --- Stage 6: Email Fallback (non-fatal; degrades gracefully without a Hunter key) ---
        email_fallback_result = await apply_email_fallback(
            EmailFallbackInput(
                job_id=job.id, contacts=enrich_result.contacts, domain=job.normalized_domain
            ),
            _try_build_hunter_client(),
        )

        # --- Stage 7: Normalize ---
        normalized_contacts = normalize_contacts(email_fallback_result)

        # --- Stage 8: Dedup ---
        dedup_result = await dedup_contacts(
            DedupInput(company_id=company.id, contacts=normalized_contacts), session
        )

        # --- Stage 9: Persist + Surface ---
        await persist_contacts_and_complete(
            job, company.id, dedup_result.new_contacts, PipelineStage.PERSIST.value, session, ws_manager
        )

    async def _set_status(self, job: Job, session: AsyncSession, stage: PipelineStage) -> None:
        job.status = STAGE_TO_JOB_STATUS[stage]
        await session.commit()
        await ws_manager.broadcast(
            {"type": "job_update", "job_id": job.id, "status": job.status.value}
        )

    async def _fail_job(
        self, job: Job, session: AsyncSession, stage: PipelineStage, message: str
    ) -> None:
        job.status = JobStatus.FAILED
        job.error_message = f"[{stage.value}] {message}"
        await session.commit()
        logger.error("job %s failed at stage %s: %s", job.id, stage.value, message)
        await ws_manager.broadcast(
            {
                "type": "job_update",
                "job_id": job.id,
                "status": job.status.value,
                "error": job.error_message,
            }
        )

    async def _with_retry(
        self, stage: PipelineStage, coro_factory: Callable[[], Awaitable[T]]
    ) -> T:
        last_message = "unknown error"
        for attempt in range(STAGE_MAX_RETRIES + 1):
            try:
                return await coro_factory()
            except StageFailure as failure:
                last_message = str(failure)
            except Exception as exc:  # noqa: BLE001 - normalize any client error into a retryable failure
                last_message = str(exc)

            if attempt < STAGE_MAX_RETRIES:
                await asyncio.sleep(STAGE_RETRY_BACKOFF_SECONDS * (attempt + 1))

        raise StageFailure(stage, last_message)


def _try_build_hunter_client() -> HunterEmailClient | None:
    try:
        return HunterEmailClient()
    except RuntimeError:
        return None


job_queue = JobQueue(concurrency_limit=settings.job_concurrency_limit)

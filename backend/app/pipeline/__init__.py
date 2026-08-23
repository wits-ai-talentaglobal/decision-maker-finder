import enum

from app.models import JobStatus

# NOTE: "Campaign A High Risk Workflow" in the source n8n export was the campaign's
# own internal label for its entire lead-gen pipeline (see the workflow's sticky
# note) — not a distinct conditional branch inside a larger workflow. There's no
# separate "high risk" logic to reconstruct; this pipeline covers the whole thing.


class PipelineStage(str, enum.Enum):
    """Pipeline stages, used for logging/error attribution.

    Stage 1 branches on whether a LinkedIn company page was resolved:
    Path A (found) -> SCRAPE_EMPLOYEES then VALIDATE_CANDIDATES (one classification
    call per scraped employee). Path B (not found) -> IDENTIFY_DECISION_MAKERS
    (direct AI web search for candidates; the qualification check is embedded in
    the search prompt itself, so there's no separate validation pass for this path).
    Both paths converge at ENRICH_CONTACTS onward.

    Several stages share a single user-visible JobStatus (see STAGE_TO_JOB_STATUS)
    because the spec's UI progress model is coarser than the internal stage split.
    """

    RESOLVE_IDENTITY = "resolve_identity"
    SCRAPE_EMPLOYEES = "scrape_employees"
    IDENTIFY_DECISION_MAKERS = "identify_decision_makers"
    VALIDATE_CANDIDATES = "validate_candidates"
    ENRICH_CONTACTS = "enrich_contacts"
    EMAIL_FALLBACK = "email_fallback"
    NORMALIZE = "normalize"
    DEDUP = "dedup"
    PERSIST = "persist"


STAGE_TO_JOB_STATUS: dict[PipelineStage, JobStatus] = {
    PipelineStage.RESOLVE_IDENTITY: JobStatus.RESOLVING_COMPANY,
    PipelineStage.SCRAPE_EMPLOYEES: JobStatus.SCRAPING_EMPLOYEES,
    PipelineStage.IDENTIFY_DECISION_MAKERS: JobStatus.IDENTIFYING_DECISION_MAKERS,
    PipelineStage.VALIDATE_CANDIDATES: JobStatus.IDENTIFYING_DECISION_MAKERS,
    PipelineStage.ENRICH_CONTACTS: JobStatus.ENRICHING_CONTACTS,
    PipelineStage.EMAIL_FALLBACK: JobStatus.ENRICHING_CONTACTS,
    PipelineStage.NORMALIZE: JobStatus.ENRICHING_CONTACTS,
    PipelineStage.DEDUP: JobStatus.ENRICHING_CONTACTS,
    PipelineStage.PERSIST: JobStatus.ENRICHING_CONTACTS,
}


class StageFailure(Exception):
    """Raised by a stage to fail its job without stopping other jobs.

    Caught by queue.py, which records `stage` and `str(exception)` on the Job and
    moves on to the next job in the queue.
    """

    def __init__(self, stage: PipelineStage, message: str) -> None:
        self.stage = stage
        super().__init__(message)

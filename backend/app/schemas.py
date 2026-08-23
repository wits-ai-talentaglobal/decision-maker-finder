from datetime import datetime

from pydantic import BaseModel

from app.models import JobStatus

# ---------------------------------------------------------------------------
# API request/response models
# ---------------------------------------------------------------------------


class JobSubmitRequest(BaseModel):
    urls_text: str
    confirmed: bool = False


class BatchEstimate(BaseModel):
    """Returned instead of enqueueing when a batch exceeds the confirmation threshold."""

    url_count: int
    invalid_entries: list[str]
    estimated_apify_calls: int
    estimated_llm_calls: int
    estimated_apollo_calls: int
    estimated_hunter_calls: int
    requires_confirmation: bool


class ClearJobsResult(BaseModel):
    deleted_jobs: int
    deleted_companies: int
    deleted_contacts: int


class ContactOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    title: str
    linkedin_url: str | None
    apollo_id: str | None
    email: str | None
    email_status: str | None
    phone: str | None
    source_stage: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyOut(BaseModel):
    id: int
    name: str
    website: str
    linkedin_url: str | None
    city: str | None
    state: str | None
    resolved_confidence: float | None
    contacts: list[ContactOut] = []

    model_config = {"from_attributes": True}


class JobOut(BaseModel):
    id: int
    input_url: str
    normalized_domain: str
    status: JobStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    company: CompanyOut | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Inter-stage typed contracts (Pydantic, not loose dicts)
# ---------------------------------------------------------------------------


class IdentityInput(BaseModel):
    job_id: int
    normalized_domain: str


class IdentityResult(BaseModel):
    company_name: str
    website: str
    linkedin_url: str | None
    city: str | None
    state: str | None
    resolved_confidence: float


class EmployeesInput(BaseModel):
    job_id: int
    company_name: str
    linkedin_url: str | None


class ScrapedEmployee(BaseModel):
    name: str
    position: str
    linkedin_profile: str


class EmployeesResult(BaseModel):
    employees: list[ScrapedEmployee]


class DecisionMakerCandidate(BaseModel):
    name: str
    position: str
    # None when a candidate was found via direct AI search but no confirmable
    # LinkedIn profile URL — Apollo enrichment is skipped for these (Stage 5),
    # and they're discarded downstream if Hunter can't find an email either.
    linkedin_profile: str | None = None


# --- Path A: LinkedIn company page found -> scrape employees, classify each ---


class ClassifyEmployeesInput(BaseModel):
    job_id: int
    employees: list[ScrapedEmployee]
    active_titles: list[str]


class ClassifyEmployeesResult(BaseModel):
    validated: list[DecisionMakerCandidate]


# --- Path B: no LinkedIn company page found -> search for candidates directly ---


class AiSearchInput(BaseModel):
    job_id: int
    company_name: str
    domain: str
    active_titles: list[str]


class AiSearchResult(BaseModel):
    candidates: list[DecisionMakerCandidate]


class EnrichInput(BaseModel):
    job_id: int
    candidates: list[DecisionMakerCandidate]
    domain: str


class EnrichedContact(BaseModel):
    first_name: str
    last_name: str
    title: str
    linkedin_url: str | None
    apollo_id: str | None
    email: str | None
    email_status: str | None = None
    phone: str | None


class EnrichResult(BaseModel):
    contacts: list[EnrichedContact]


class EmailFallbackInput(BaseModel):
    job_id: int
    contacts: list[EnrichedContact]
    domain: str


class EmailFallbackResult(BaseModel):
    contacts: list[EnrichedContact]


class NormalizedContact(BaseModel):
    first_name: str
    last_name: str
    title: str
    linkedin_url: str | None
    apollo_id: str | None
    email: str | None
    email_status: str | None
    phone: str | None  # digits only


class DedupInput(BaseModel):
    company_id: int
    contacts: list[NormalizedContact]


class DedupResult(BaseModel):
    new_contacts: list[NormalizedContact]
    skipped_duplicates: int

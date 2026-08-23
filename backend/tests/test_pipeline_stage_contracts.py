"""Tests each pipeline stage's typed input/output contract in isolation, using fake
integration clients — no live external API calls, no API keys required."""

import pytest

from app.pipeline import PipelineStage, StageFailure
from app.pipeline.stage1_identity import _looks_dead_or_parked, resolve_company_identity
from app.pipeline.stage2_employees import scrape_employees
from app.pipeline.stage3_identify import search_decision_makers_directly
from app.pipeline.stage4_validate import validate_candidates
from app.pipeline.stage5_enrich import enrich_contacts
from app.pipeline.stage6_email_fallback import apply_email_fallback
from app.pipeline.stage7_normalize import normalize_contacts
from app.pipeline.stage8_dedup import dedup_contacts
from app.schemas import (
    AiSearchInput,
    ClassifyEmployeesInput,
    DecisionMakerCandidate,
    DedupInput,
    EmailFallbackInput,
    EmployeesInput,
    EnrichedContact,
    EnrichInput,
    IdentityInput,
    ScrapedEmployee,
)
from tests.conftest import FakeClassifierLLMClient, FakeSearchLLMClient


@pytest.mark.asyncio
async def test_stage1_resolves_identity(fake_search_llm, monkeypatch):
    async def fake_fetch_site_snapshot(domain):
        return "Acme Corp - Home", "Welcome to Acme Corp, the best widgets in Austin, TX."

    monkeypatch.setattr(
        "app.pipeline.stage1_identity.fetch_site_snapshot", fake_fetch_site_snapshot
    )

    result = await resolve_company_identity(
        IdentityInput(job_id=1, normalized_domain="acme.com"), fake_search_llm
    )
    assert result.company_name == "Acme Corp"
    assert result.linkedin_url == "https://linkedin.com/company/acme"


def test_stage1_detects_parked_domain():
    assert _looks_dead_or_parked("Domain For Sale", "buy this domain now") is True
    assert _looks_dead_or_parked(None, None) is True
    assert _looks_dead_or_parked("Acme Corp", "we make widgets") is False


@pytest.mark.asyncio
async def test_stage2_raises_on_empty_scrape(fake_employee_scraper):
    with pytest.raises(StageFailure) as exc_info:
        await scrape_employees(
            EmployeesInput(job_id=1, company_name="Acme", linkedin_url=None),
            fake_employee_scraper,
        )
    assert exc_info.value.stage == PipelineStage.SCRAPE_EMPLOYEES
    assert "no employees found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_stage3_returns_candidates_from_direct_search():
    candidates = [
        DecisionMakerCandidate(name="Jane Doe", position="Owner", linkedin_profile="https://linkedin.com/in/jane")
    ]
    llm = FakeSearchLLMClient(search_candidates=candidates)

    result = await search_decision_makers_directly(
        AiSearchInput(job_id=1, company_name="Acme", domain="acme.com", active_titles=["Owner"]), llm
    )
    assert result.candidates == candidates


@pytest.mark.asyncio
async def test_stage3_empty_search_result_is_not_a_failure():
    llm = FakeSearchLLMClient(search_candidates=[])

    result = await search_decision_makers_directly(
        AiSearchInput(job_id=1, company_name="Acme", domain="acme.com", active_titles=["Owner"]), llm
    )
    assert result.candidates == []


@pytest.mark.asyncio
async def test_stage4_keeps_employees_whose_title_matches():
    employees = [ScrapedEmployee(name="Jane Doe", position="Sales Manager", linkedin_profile="https://linkedin.com/in/jane")]
    llm = FakeClassifierLLMClient(validate_result=True)

    result = await validate_candidates(
        ClassifyEmployeesInput(job_id=1, employees=employees, active_titles=["Sales Manager"]), llm
    )
    assert len(result.validated) == 1
    assert result.validated[0].name == "Jane Doe"


@pytest.mark.asyncio
async def test_stage4_drops_employees_whose_title_does_not_match():
    employees = [ScrapedEmployee(name="Jane Doe", position="Receptionist", linkedin_profile="https://linkedin.com/in/jane")]
    llm = FakeClassifierLLMClient(validate_result=False)

    result = await validate_candidates(
        ClassifyEmployeesInput(job_id=1, employees=employees, active_titles=["Sales Manager"]), llm
    )
    assert result.validated == []


class FakeApolloClient:
    async def match_person(self, linkedin_url, name, title):
        return EnrichedContact(
            first_name="Jane", last_name="Doe", title=title,
            linkedin_url=linkedin_url, apollo_id="apollo-1", email="jane@acme.com", phone="5551234567",
        )


@pytest.mark.asyncio
async def test_stage5_skips_apollo_for_candidate_with_no_linkedin_profile():
    candidate = DecisionMakerCandidate(name="Jane Doe", position="Owner", linkedin_profile=None)

    result = await enrich_contacts(
        EnrichInput(job_id=1, candidates=[candidate], domain="acme.com"), FakeApolloClient()
    )
    assert len(result.contacts) == 1
    assert result.contacts[0].linkedin_url is None
    assert result.contacts[0].apollo_id is None


@pytest.mark.asyncio
async def test_stage5_enriches_candidate_with_linkedin_profile_via_apollo():
    candidate = DecisionMakerCandidate(
        name="Jane Doe", position="Owner", linkedin_profile="https://linkedin.com/in/jane"
    )

    result = await enrich_contacts(
        EnrichInput(job_id=1, candidates=[candidate], domain="acme.com"), FakeApolloClient()
    )
    assert result.contacts[0].apollo_id == "apollo-1"


@pytest.mark.asyncio
async def test_stage6_no_hunter_client_keeps_contact_with_linkedin_url():
    contact = EnrichedContact(
        first_name="Jane", last_name="Doe", title="Owner",
        linkedin_url="https://linkedin.com/in/jane", apollo_id=None, email=None, phone=None,
    )
    result = await apply_email_fallback(
        EmailFallbackInput(job_id=1, contacts=[contact], domain="acme.com"), None
    )
    assert result.contacts == [contact]


@pytest.mark.asyncio
async def test_stage6_no_hunter_client_discards_contact_with_no_linkedin_and_no_email():
    contact = EnrichedContact(
        first_name="Jane", last_name="Doe", title="Owner",
        linkedin_url=None, apollo_id=None, email=None, phone=None,
    )
    result = await apply_email_fallback(
        EmailFallbackInput(job_id=1, contacts=[contact], domain="acme.com"), None
    )
    assert result.contacts == []


class FakeHunterClient:
    def __init__(self, email="jane@acme.com", status="valid"):
        self._email = email
        self._status = status

    async def find_email(self, domain, first_name, last_name):
        return self._email

    async def verify_email(self, email):
        return self._status


@pytest.mark.asyncio
async def test_stage6_finds_email_for_linkedin_less_contact():
    contact = EnrichedContact(
        first_name="Jane", last_name="Doe", title="Owner",
        linkedin_url=None, apollo_id=None, email=None, phone=None,
    )
    result = await apply_email_fallback(
        EmailFallbackInput(job_id=1, contacts=[contact], domain="acme.com"), FakeHunterClient()
    )
    assert len(result.contacts) == 1
    assert result.contacts[0].email == "jane@acme.com"
    assert result.contacts[0].email_status == "valid"


def test_stage7_normalizes_phone_and_casing():
    from app.schemas import EmailFallbackResult

    contact = EnrichedContact(
        first_name="jane", last_name="DOE", title=" Sales Manager ",
        linkedin_url="https://linkedin.com/in/jane", apollo_id="abc123",
        email="Jane.Doe@Example.COM", phone="+1 (512) 555-0100", email_status="valid",
    )
    normalized = normalize_contacts(EmailFallbackResult(contacts=[contact]))
    assert normalized[0].first_name == "Jane"
    assert normalized[0].last_name == "Doe"
    assert normalized[0].phone == "15125550100"
    assert normalized[0].email == "jane.doe@example.com"
    assert normalized[0].email_status == "valid"


@pytest.mark.asyncio
async def test_stage8_dedup_skips_existing_linkedin_url(db_session):
    from app.models import Company, Contact, Job, JobStatus
    from app.schemas import NormalizedContact

    job = Job(input_url="acme.com", normalized_domain="acme.com", status=JobStatus.QUEUED)
    db_session.add(job)
    await db_session.flush()
    company = Company(job_id=job.id, name="Acme", website="acme.com")
    db_session.add(company)
    await db_session.flush()
    db_session.add(
        Contact(
            company_id=company.id, first_name="Jane", last_name="Doe", title="Sales Manager",
            linkedin_url="https://linkedin.com/in/jane", source_stage="persist",
        )
    )
    await db_session.commit()

    new_contact = NormalizedContact(
        first_name="Jane", last_name="Doe", title="Sales Manager",
        linkedin_url="https://linkedin.com/in/jane", apollo_id=None,
        email=None, email_status=None, phone=None,
    )
    result = await dedup_contacts(
        DedupInput(company_id=company.id, contacts=[new_contact]), db_session
    )
    assert result.new_contacts == []
    assert result.skipped_duplicates == 1


@pytest.mark.asyncio
async def test_stage8_dedup_does_not_treat_two_linkedin_less_contacts_as_duplicates(db_session):
    from app.models import Company, Job, JobStatus
    from app.schemas import NormalizedContact

    job = Job(input_url="acme.com", normalized_domain="acme.com", status=JobStatus.QUEUED)
    db_session.add(job)
    await db_session.flush()
    company = Company(job_id=job.id, name="Acme", website="acme.com")
    db_session.add(company)
    await db_session.flush()

    contacts = [
        NormalizedContact(
            first_name="Jane", last_name="Doe", title="Owner", linkedin_url=None,
            apollo_id=None, email="jane@acme.com", email_status=None, phone=None,
        ),
        NormalizedContact(
            first_name="John", last_name="Doe", title="Owner", linkedin_url=None,
            apollo_id=None, email="john@acme.com", email_status=None, phone=None,
        ),
    ]
    result = await dedup_contacts(DedupInput(company_id=company.id, contacts=contacts), db_session)
    assert len(result.new_contacts) == 2
    assert result.skipped_duplicates == 0

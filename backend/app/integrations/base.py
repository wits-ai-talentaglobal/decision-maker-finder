"""Typed provider interfaces. Each pipeline stage depends on one of these Protocols,
never on a concrete client — swapping a provider means writing a new class that
satisfies the Protocol and wiring it in, without touching pipeline logic.
"""

from typing import Protocol

from app.schemas import DecisionMakerCandidate, EnrichedContact, ScrapedEmployee


class SearchLLMClient(Protocol):
    """Company identity resolution and decision-maker search via a web-search LLM."""

    async def resolve_company_identity(
        self, domain: str, site_title: str | None, site_text: str | None
    ) -> tuple[str, str | None, str | None, str | None, float]:
        """Stage 1. Returns (company_name, linkedin_url_or_None, city, state, confidence).

        linkedin_url must only be returned if it is verifiably present in the
        underlying search results/citations — implementations must enforce this,
        never trust the LLM's free-text claim alone.
        """
        ...

    async def search_decision_makers(
        self, company_name: str, domain: str, active_titles: list[str]
    ) -> list[DecisionMakerCandidate]:
        """Path B (no LinkedIn company page resolved): search the web directly for
        likely decision-makers, since there's no employee list to classify against.

        Each candidate's linkedin_profile must only be set if it is verifiably
        present in search citations — same anti-hallucination rule as Stage 1.
        """
        ...


class EmployeeScraperClient(Protocol):
    """Stage 2: pull up to N employees for a company from LinkedIn."""

    async def scrape_employees(
        self, company_name: str, linkedin_url: str | None, limit: int = 25
    ) -> list[ScrapedEmployee]: ...


class ClassifierLLMClient(Protocol):
    """Path A: deterministic per-employee title classification against the taxonomy."""

    async def validate_candidate(
        self, candidate: DecisionMakerCandidate, active_titles: list[str]
    ) -> bool: ...


class ContactEnrichmentClient(Protocol):
    """Stage 5: enrich a candidate's contact info from their LinkedIn URL."""

    async def match_person(
        self, linkedin_url: str, name: str, title: str
    ) -> EnrichedContact: ...


class EmailFinderClient(Protocol):
    """Stage 6: fallback email discovery/verification when enrichment has no email."""

    async def find_email(self, domain: str, first_name: str, last_name: str) -> str | None: ...

    async def verify_email(self, email: str) -> str | None:
        """Returns a status string (e.g. 'valid', 'risky', 'invalid') or None if unavailable."""
        ...

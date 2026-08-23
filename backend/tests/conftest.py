import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models import Base


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


class FakeSearchLLMClient:
    """Fake OpenRouter/Sonar client for tests — no live calls."""

    def __init__(
        self,
        name="Acme Corp",
        linkedin_url="https://linkedin.com/company/acme",
        city="Austin",
        state="TX",
        confidence=0.9,
        search_candidates=None,
    ):
        self._response = (name, linkedin_url, city, state, confidence)
        self._search_candidates = search_candidates or []

    async def resolve_company_identity(self, domain, site_title, site_text):
        return self._response

    async def search_decision_makers(self, company_name, domain, active_titles):
        return self._search_candidates


class FakeEmployeeScraperClient:
    def __init__(self, employees=None):
        self._employees = employees or []

    async def scrape_employees(self, company_name, linkedin_url, limit=25):
        return self._employees[:limit]


class FakeClassifierLLMClient:
    def __init__(self, validate_result=True):
        self._validate_result = validate_result

    async def validate_candidate(self, candidate, active_titles):
        return self._validate_result


@pytest.fixture
def fake_search_llm():
    return FakeSearchLLMClient()


@pytest.fixture
def fake_employee_scraper():
    return FakeEmployeeScraperClient()


@pytest.fixture
def fake_classifier_llm():
    return FakeClassifierLLMClient()

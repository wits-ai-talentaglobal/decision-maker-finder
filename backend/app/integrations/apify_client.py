"""Stage 2: Apify actor call to scrape a company's LinkedIn employees.

harvestapi/linkedin-company-employees requires a LinkedIn *company* URL (not a
company name) as input — if Stage 1 couldn't resolve one, this stage can't run.
"""

import httpx

from app.config import settings
from app.schemas import ScrapedEmployee

_APIFY_RUN_SYNC_URL_TEMPLATE = (
    "https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items"
)


class NoLinkedInUrlError(RuntimeError):
    pass


class ApifyEmployeeScraperClient:
    def __init__(self) -> None:
        if not settings.apify_api_token:
            raise RuntimeError("APIFY_API_TOKEN is not set")
        self._token = settings.apify_api_token
        self._actor_id = settings.apify_employees_actor_id.replace("/", "~")

    async def scrape_employees(
        self, company_name: str, linkedin_url: str | None, limit: int = 25
    ) -> list[ScrapedEmployee]:
        if not linkedin_url:
            raise NoLinkedInUrlError(
                f"no LinkedIn company URL resolved for {company_name!r}; "
                "harvestapi/linkedin-company-employees requires one"
            )

        url = _APIFY_RUN_SYNC_URL_TEMPLATE.format(actor_id=self._actor_id)
        run_input = {
            "companies": [linkedin_url],
            "maxItems": limit,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                # Token passed as a bearer header, not a query param, so it never
                # ends up in request-URL logs (httpx/uvicorn log the URL at INFO).
                headers={"Authorization": f"Bearer {self._token}"},
                json=run_input,
            )
            response.raise_for_status()
            items = response.json()

        employees: list[ScrapedEmployee] = []
        for item in items:
            first_name = item.get("firstName") or ""
            last_name = item.get("lastName") or ""
            name = f"{first_name} {last_name}".strip() or item.get("fullName") or ""
            position = item.get("headline") or item.get("position") or ""
            profile = item.get("linkedinUrl") or item.get("profileUrl") or ""
            if name and profile:
                employees.append(ScrapedEmployee(name=name, position=position, linkedin_profile=profile))

        return employees[:limit]

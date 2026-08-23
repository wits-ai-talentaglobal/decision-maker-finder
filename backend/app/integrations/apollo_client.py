"""Stage 5: Apollo.io /people/match contact enrichment."""

import httpx

from app.config import settings
from app.schemas import EnrichedContact

_APOLLO_MATCH_URL = "https://api.apollo.io/api/v1/people/match"


class ApolloEnrichmentClient:
    def __init__(self) -> None:
        if not settings.apollo_api_key:
            raise RuntimeError("APOLLO_API_KEY is not set")
        self._api_key = settings.apollo_api_key

    async def match_person(self, linkedin_url: str, name: str, title: str) -> EnrichedContact:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                _APOLLO_MATCH_URL,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self._api_key,
                },
                json={"linkedin_url": linkedin_url},
            )
            response.raise_for_status()
            payload = response.json()

        person = payload.get("person") or {}
        first_name = person.get("first_name") or _split_name(name)[0]
        last_name = person.get("last_name") or _split_name(name)[1]

        return EnrichedContact(
            first_name=first_name,
            last_name=last_name,
            title=person.get("title") or title,
            linkedin_url=linkedin_url,
            apollo_id=person.get("id"),
            email=person.get("email"),
            phone=(person.get("organization") or {}).get("phone")
            or person.get("phone_number"),
        )


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(" ", 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]

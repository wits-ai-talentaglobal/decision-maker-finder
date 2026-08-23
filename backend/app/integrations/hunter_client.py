"""Stage 6: Hunter.io email fallback (emailFinder + optional emailVerifier).

HUNTER_API_KEY is not yet provisioned for this project — this client is a complete,
typed implementation of EmailFinderClient; it simply raises at construction time
until a key is added to .env. The pipeline stage handles that by skipping the
fallback gracefully (see stage6_email_fallback.py), so its absence never blocks
Stages 7-9 for a job.
"""

import httpx

from app.config import settings

_HUNTER_FINDER_URL = "https://api.hunter.io/v2/email-finder"
_HUNTER_VERIFIER_URL = "https://api.hunter.io/v2/email-verifier"


class HunterEmailClient:
    def __init__(self) -> None:
        if not settings.hunter_api_key:
            raise RuntimeError("HUNTER_API_KEY is not set")
        self._api_key = settings.hunter_api_key

    async def find_email(self, domain: str, first_name: str, last_name: str) -> str | None:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                _HUNTER_FINDER_URL,
                params={
                    "domain": domain,
                    "first_name": first_name,
                    "last_name": last_name,
                    "api_key": self._api_key,
                },
            )
            response.raise_for_status()
            payload = response.json()

        return (payload.get("data") or {}).get("email")

    async def verify_email(self, email: str) -> str | None:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                _HUNTER_VERIFIER_URL,
                params={"email": email, "api_key": self._api_key},
            )
            response.raise_for_status()
            payload = response.json()

        return (payload.get("data") or {}).get("status")

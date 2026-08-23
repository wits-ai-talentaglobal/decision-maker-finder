"""Stage 1: Company Identity Resolution.

Fetches site metadata, asks a web-search-capable LLM (OpenRouter/Sonar) to confirm
the official company name and LinkedIn page (citation-backed only), best-effort
extracts city/state, and runs a liveness/sanity check before any paid API is called
downstream. Raises StageFailure("no company identity found") on failure, per spec.
"""

import re

import httpx

from app.integrations.base import SearchLLMClient
from app.pipeline import PipelineStage, StageFailure
from app.schemas import IdentityInput, IdentityResult

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_PARKED_MARKERS = (
    "domain is for sale",
    "buy this domain",
    "this domain is parked",
    "future home of something quite cool",
)


async def fetch_site_snapshot(domain: str) -> tuple[str | None, str | None]:
    """Best-effort fetch of the homepage; returns (title, text_excerpt) or (None, None)
    if the site can't be reached at all (liveness failure is raised separately)."""
    for scheme in ("https", "http"):
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(f"{scheme}://{domain}")
                if response.status_code >= 400:
                    continue
                html = response.text
                title_match = _TITLE_RE.search(html)
                title = title_match.group(1).strip() if title_match else None
                text_excerpt = re.sub(r"<[^>]+>", " ", html)[:2000]
                return title, text_excerpt
        except httpx.HTTPError:
            continue
    return None, None


def _looks_dead_or_parked(title: str | None, text: str | None) -> bool:
    if title is None and text is None:
        return True
    haystack = f"{title or ''} {text or ''}".lower()
    return any(marker in haystack for marker in _PARKED_MARKERS)


async def resolve_company_identity(
    stage_input: IdentityInput, llm: SearchLLMClient
) -> IdentityResult:
    title, text = await fetch_site_snapshot(stage_input.normalized_domain)

    if _looks_dead_or_parked(title, text):
        raise StageFailure(
            PipelineStage.RESOLVE_IDENTITY,
            f"no company identity found: {stage_input.normalized_domain} appears dead or parked",
        )

    try:
        company_name, linkedin_url, city, state, confidence = await llm.resolve_company_identity(
            stage_input.normalized_domain, title, text
        )
    except Exception as exc:
        raise StageFailure(
            PipelineStage.RESOLVE_IDENTITY, f"no company identity found: {exc}"
        ) from exc

    if not company_name:
        raise StageFailure(
            PipelineStage.RESOLVE_IDENTITY,
            f"no company identity found for {stage_input.normalized_domain}",
        )

    return IdentityResult(
        company_name=company_name,
        website=stage_input.normalized_domain,
        linkedin_url=linkedin_url,
        city=city,
        state=state,
        resolved_confidence=confidence,
    )

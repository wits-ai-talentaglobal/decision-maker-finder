"""OpenRouter using Perplexity Sonar (native web search + citations).

Used for the two web-search-requiring steps in the pipeline: Stage 1 (company
identity + LinkedIn resolution) and the Path B fallback (searching directly for
decision-makers when no LinkedIn company page was found). The anti-hallucination
rule requires that any LinkedIn URL we accept literally appears in the search
results the model consulted, so both prompts demand a response format that
exposes citations/sources, not just free-text prose.
"""

import json
import re

import httpx

from app.config import settings
from app.schemas import DecisionMakerCandidate

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

_IDENTITY_SYSTEM_PROMPT = (
    "You are a company research assistant. Given a website domain, use web search to "
    "identify: the official company name, the official company LinkedIn page URL, and "
    "the company's city/state if discoverable from its site or public listings. "
    "Respond with ONLY a JSON object: "
    '{"company_name": str, "linkedin_url": str|null, "city": str|null, "state": str|null, '
    '"confidence": float between 0 and 1}. '
    "If you cannot confidently find a piece of information, use null for it. "
    "Never invent a LinkedIn URL you did not see in search results."
)

_DECISION_MAKER_SEARCH_SYSTEM_PROMPT = (
    "You are a B2B researcher. No LinkedIn company page could be confirmed for this "
    "business, so use web search to directly identify people who CURRENTLY hold one of "
    "the given leadership titles (or a clearly equivalent/more senior variant) at this "
    "company. Respond with ONLY a JSON object: "
    '{"candidates": [{"name": str, "position": str, "linkedin_profile": str|null}]}. '
    "Include a linkedin_profile URL only if it literally appears in your search results — "
    "never invent or guess one; use null if you found the person but not a confirmable "
    "profile URL. Do not include people who do not clearly hold a qualifying title. If "
    'you find no qualifying people, respond {"candidates": []}.'
)


class OpenRouterSonarClient:
    def __init__(self) -> None:
        if not settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        self._api_key = settings.openrouter_api_key
        self._model = settings.openrouter_model

    async def resolve_company_identity(
        self, domain: str, site_title: str | None, site_text: str | None
    ) -> tuple[str, str | None, str | None, str | None, float]:
        user_prompt = (
            f"Website domain: {domain}\n"
            f"Site title (if fetched): {site_title or 'unknown'}\n"
            f"Site excerpt (if fetched): {(site_text or 'unknown')[:1000]}\n\n"
            "Identify the official company name, LinkedIn company page, and city/state."
        )

        message, payload = await self._complete(_IDENTITY_SYSTEM_PROMPT, user_prompt)
        parsed = _parse_json_object(message.get("content", ""))
        citation_urls = _extract_citation_urls(payload, message)

        company_name = parsed.get("company_name") or domain
        linkedin_url = parsed.get("linkedin_url")
        city = parsed.get("city")
        state = parsed.get("state")
        confidence = float(parsed.get("confidence") or 0.0)

        if linkedin_url and not _url_in_citations(linkedin_url, citation_urls):
            # Anti-hallucination guard: reject any LinkedIn URL not backed by a citation.
            linkedin_url = None
            confidence = min(confidence, 0.5)

        return company_name, linkedin_url, city, state, confidence

    async def search_decision_makers(
        self, company_name: str, domain: str, active_titles: list[str]
    ) -> list[DecisionMakerCandidate]:
        user_prompt = (
            f"Company: {company_name}\n"
            f"Website: {domain}\n\n"
            "Qualifying leadership titles:\n" + "\n".join(f"- {t}" for t in active_titles)
        )

        message, payload = await self._complete(
            _DECISION_MAKER_SEARCH_SYSTEM_PROMPT, user_prompt
        )
        parsed = _parse_json_object(message.get("content", ""))
        citation_urls = _extract_citation_urls(payload, message)

        candidates = []
        for item in parsed.get("candidates", []):
            linkedin_profile = item.get("linkedin_profile")
            if linkedin_profile and not _url_in_citations(linkedin_profile, citation_urls):
                # Anti-hallucination guard: same rule as Stage 1's LinkedIn check.
                linkedin_profile = None
            candidates.append(
                DecisionMakerCandidate(
                    name=item.get("name", ""),
                    position=item.get("position", ""),
                    linkedin_profile=linkedin_profile,
                )
            )

        return [c for c in candidates if c.name]

    async def _complete(self, system_prompt: str, user_prompt: str) -> tuple[dict, dict]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                _OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )
            response.raise_for_status()
            payload = response.json()

        message = payload["choices"][0]["message"]
        return message, payload


def _parse_json_object(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {}


def _extract_citation_urls(payload: dict, message: dict) -> list[str]:
    urls: list[str] = []
    for key in ("citations",):
        value = payload.get(key)
        if isinstance(value, list):
            urls.extend(str(u) for u in value)

    annotations = message.get("annotations") or []
    for annotation in annotations:
        url = (annotation.get("url_citation") or {}).get("url")
        if url:
            urls.append(str(url))

    return urls


def _url_in_citations(url: str, citations: list[str]) -> bool:
    normalized = url.rstrip("/").lower()
    return any(normalized in c.rstrip("/").lower() or c.rstrip("/").lower() in normalized for c in citations)

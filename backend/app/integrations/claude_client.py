"""Path A LLM: Claude API direct, for deterministic per-employee title classification.

No web search needed here — this is a closed-set classification task (does this
scraped employee's title match the taxonomy?), one call per employee, matching the
reference workflow's single "Validate Job Title" pass (no separate batch-extraction
step precedes it — employees come straight from the LinkedIn scrape).
"""

import json
import re

import httpx

from app.config import settings
from app.schemas import DecisionMakerCandidate

_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"


class ClaudeClassifierClient:
    def __init__(self) -> None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self._api_key = settings.anthropic_api_key
        self._model = settings.anthropic_model

    async def validate_candidate(
        self, candidate: DecisionMakerCandidate, active_titles: list[str]
    ) -> bool:
        prompt = (
            "Leadership title taxonomy:\n"
            + "\n".join(f"- {t}" for t in active_titles)
            + f"\n\nCandidate title: {candidate.position!r}\n"
            "Does this title match (or is it a clear variant of) one of the taxonomy "
            'titles? Respond with ONLY {"match": true} or {"match": false}.'
        )
        content = await self._complete(prompt)
        parsed = _parse_json_object(content)
        return bool(parsed.get("match", False))

    async def _complete(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                _ANTHROPIC_URL,
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": _ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json={
                    "model": self._model,
                    "max_tokens": 2048,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            payload = response.json()

        blocks = payload.get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


def _parse_json_object(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        return json.loads(match.group(0)) if match else {}

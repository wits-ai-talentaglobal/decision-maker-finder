"""Stage 3 (Path B): Decision-Maker Identification via direct AI search.

Used only when Stage 1 could not resolve a LinkedIn company page — there's no
employee list to scrape, so a web-search LLM identifies likely decision-makers
directly, using the leadership title taxonomy as its own search/filter criteria
(the qualification check happens inside the search prompt, not as a separate
follow-up validation call — matching the reference workflow's AI-search branch).

An empty result here is not a failure: it just means this job produces zero
contacts, same as Path A finding zero qualifying employees.
"""

from app.integrations.base import SearchLLMClient
from app.pipeline import PipelineStage, StageFailure
from app.schemas import AiSearchInput, AiSearchResult


async def search_decision_makers_directly(
    stage_input: AiSearchInput, llm: SearchLLMClient
) -> AiSearchResult:
    try:
        candidates = await llm.search_decision_makers(
            stage_input.company_name, stage_input.domain, stage_input.active_titles
        )
    except Exception as exc:
        raise StageFailure(
            PipelineStage.IDENTIFY_DECISION_MAKERS, f"decision-maker search failed: {exc}"
        ) from exc

    return AiSearchResult(candidates=candidates)

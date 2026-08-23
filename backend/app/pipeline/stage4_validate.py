"""Stage 4 (Path A): Per-Employee Title Classification.

One deterministic LLM call per scraped employee — matches the reference
workflow's single "Validate Job Title" pass. There is no separate batch
extraction step first: every employee from the scrape is checked directly.
"""

from app.integrations.base import ClassifierLLMClient
from app.logging_conf import get_stage_logger
from app.pipeline import PipelineStage
from app.schemas import ClassifyEmployeesInput, ClassifyEmployeesResult, DecisionMakerCandidate


async def validate_candidates(
    stage_input: ClassifyEmployeesInput, llm: ClassifierLLMClient
) -> ClassifyEmployeesResult:
    logger = get_stage_logger(
        __name__, stage_input.job_id, PipelineStage.VALIDATE_CANDIDATES.value
    )
    validated: list[DecisionMakerCandidate] = []

    for employee in stage_input.employees:
        candidate = DecisionMakerCandidate(
            name=employee.name,
            position=employee.position,
            linkedin_profile=employee.linkedin_profile,
        )
        try:
            is_match = await llm.validate_candidate(candidate, stage_input.active_titles)
        except Exception:
            is_match = False
            logger.warning("classification errored for %r (%r) — treated as no match", employee.name, employee.position, exc_info=True)
        else:
            logger.info(
                "%s: %r -> %s", employee.name, employee.position, "MATCH" if is_match else "no match"
            )
        if is_match:
            validated.append(candidate)

    logger.info(
        "%d/%d scraped employees matched the taxonomy", len(validated), len(stage_input.employees)
    )

    return ClassifyEmployeesResult(validated=validated)

"""Stage 2: Employee Scrape via Apify (harvestapi/linkedin-company-employees or equivalent).

Raises StageFailure("no employees found") when the scrape is empty or fails, per spec.
"""

from app.integrations.base import EmployeeScraperClient
from app.pipeline import PipelineStage, StageFailure
from app.schemas import EmployeesInput, EmployeesResult

MAX_EMPLOYEES = 25


async def scrape_employees(
    stage_input: EmployeesInput, scraper: EmployeeScraperClient
) -> EmployeesResult:
    try:
        employees = await scraper.scrape_employees(
            stage_input.company_name, stage_input.linkedin_url, limit=MAX_EMPLOYEES
        )
    except Exception as exc:
        raise StageFailure(PipelineStage.SCRAPE_EMPLOYEES, f"no employees found: {exc}") from exc

    if not employees:
        raise StageFailure(
            PipelineStage.SCRAPE_EMPLOYEES,
            f"no employees found for {stage_input.company_name}",
        )

    return EmployeesResult(employees=employees)

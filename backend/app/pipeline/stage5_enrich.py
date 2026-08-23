"""Stage 5: Contact Enrichment via Apollo.io /people/match.

A candidate with no LinkedIn profile URL (Path B, no LinkedIn company page found
and none confirmable via AI search either) skips Apollo entirely — Apollo's
/people/match is keyed off the LinkedIn URL — and falls through to Stage 6
(Hunter) as its only source of contact info, matching the reference workflow.
"""

import logging

from app.integrations.base import ContactEnrichmentClient
from app.schemas import EnrichedContact, EnrichInput, EnrichResult

logger = logging.getLogger(__name__)


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(" ", 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


async def enrich_contacts(
    stage_input: EnrichInput, apollo: ContactEnrichmentClient
) -> EnrichResult:
    contacts = []
    for candidate in stage_input.candidates:
        if not candidate.linkedin_profile:
            first_name, last_name = _split_name(candidate.name)
            contacts.append(
                EnrichedContact(
                    first_name=first_name,
                    last_name=last_name,
                    title=candidate.position,
                    linkedin_url=None,
                    apollo_id=None,
                    email=None,
                    phone=None,
                )
            )
            continue

        try:
            contact = await apollo.match_person(
                candidate.linkedin_profile, candidate.name, candidate.position
            )
        except Exception:
            logger.warning("Apollo match failed for %s", candidate.linkedin_profile, exc_info=True)
            continue
        contacts.append(contact)

    return EnrichResult(contacts=contacts)

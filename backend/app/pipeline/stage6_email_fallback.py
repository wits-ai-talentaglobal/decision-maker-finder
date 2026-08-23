"""Stage 6: Email Fallback via Hunter.io when Apollo did not return an email.

Non-fatal by design for contacts that already have a LinkedIn URL: if
HUNTER_API_KEY is unset or Hunter fails, they simply keep whatever email (or
lack thereof) they had from Stage 5.

For a contact with no LinkedIn URL (Path B, no confirmable profile), Hunter is
the *only* possible source of an email — if it still can't find one, the
contact is discarded here, matching the reference workflow ("if it returns an
email, save the contact; if not, discard the person").
"""

import logging

from app.integrations.base import EmailFinderClient
from app.schemas import EmailFallbackInput, EmailFallbackResult

logger = logging.getLogger(__name__)


async def apply_email_fallback(
    stage_input: EmailFallbackInput, hunter: EmailFinderClient | None
) -> EmailFallbackResult:
    contacts = []

    for contact in stage_input.contacts:
        if contact.email:
            contacts.append(contact)  # already has an email from Stage 5 — always keep
            continue

        if hunter is None:
            if contact.linkedin_url:
                contacts.append(contact)  # Path A: keep regardless of email
            continue  # Path B with no way to find an email: discard

        try:
            found_email = await hunter.find_email(
                stage_input.domain, contact.first_name, contact.last_name
            )
        except Exception:
            logger.warning("Hunter email-finder failed for %s", contact.first_name, exc_info=True)
            found_email = None

        if not found_email:
            if contact.linkedin_url:
                contacts.append(contact)  # Path A: keep regardless of email
            continue  # Path B, still no email: discard, per spec

        email_status = None
        try:
            email_status = await hunter.verify_email(found_email)
        except Exception:
            logger.warning("Hunter email-verifier failed for %s", found_email, exc_info=True)

        contacts.append(contact.model_copy(update={"email": found_email, "email_status": email_status}))

    return EmailFallbackResult(contacts=contacts)

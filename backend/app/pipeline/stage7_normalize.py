"""Stage 7: Normalize — strip non-digit characters from phone numbers, normalize name casing."""

import re

from app.schemas import EmailFallbackResult, NormalizedContact

_NON_DIGIT_RE = re.compile(r"\D+")


def _normalize_name_part(part: str) -> str:
    return " ".join(word.capitalize() for word in part.strip().split())


def _normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    digits = _NON_DIGIT_RE.sub("", phone)
    return digits or None


def normalize_contacts(
    stage_input: EmailFallbackResult,
) -> list[NormalizedContact]:
    normalized = []
    for contact in stage_input.contacts:
        normalized.append(
            NormalizedContact(
                first_name=_normalize_name_part(contact.first_name),
                last_name=_normalize_name_part(contact.last_name),
                title=contact.title.strip(),
                linkedin_url=contact.linkedin_url,
                apollo_id=contact.apollo_id,
                email=contact.email.strip().lower() if contact.email else None,
                email_status=contact.email_status,
                phone=_normalize_phone(contact.phone),
            )
        )
    return normalized

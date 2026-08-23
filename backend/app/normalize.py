import re

_PROTOCOL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
_URL_SPLIT_RE = re.compile(r"[\s,]+")


class InvalidUrlError(ValueError):
    pass


def normalize_domain(raw_url: str) -> str:
    """Strip protocol, www., path, and trailing slashes; lowercase for dedupe.

    e.g. "https://www.Example.com/about/" -> "example.com"
    """
    url = raw_url.strip()
    if not url:
        raise InvalidUrlError(f"empty URL: {raw_url!r}")

    url = _PROTOCOL_RE.sub("", url)
    url = url.split("/", 1)[0]  # drop path
    url = url.split("?", 1)[0]
    url = url.strip().lower()
    url = url.removeprefix("www.")
    url = url.rstrip(".")

    if "." not in url or " " in url or url == "":
        raise InvalidUrlError(f"malformed URL: {raw_url!r}")

    return url


def parse_url_list(raw_text: str) -> tuple[list[str], list[str]]:
    """Parse a newline/comma/space-separated block of URLs.

    Returns (valid_normalized_domains_deduped, invalid_raw_entries).
    Order of valid entries is preserved; duplicates (post-normalization) are dropped.
    """
    entries = [e for e in _URL_SPLIT_RE.split(raw_text) if e]

    valid: list[str] = []
    invalid: list[str] = []
    seen: set[str] = set()

    for entry in entries:
        try:
            domain = normalize_domain(entry)
        except InvalidUrlError:
            invalid.append(entry)
            continue
        if domain not in seen:
            seen.add(domain)
            valid.append(domain)

    return valid, invalid

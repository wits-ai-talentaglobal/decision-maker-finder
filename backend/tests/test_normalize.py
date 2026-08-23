import pytest

from app.normalize import InvalidUrlError, normalize_domain, parse_url_list


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("https://www.Example.com/about/", "example.com"),
        ("http://example.com", "example.com"),
        ("example.com/", "example.com"),
        ("WWW.EXAMPLE.COM", "example.com"),
        ("https://example.com/path?query=1", "example.com"),
    ],
)
def test_normalize_domain(raw, expected):
    assert normalize_domain(raw) == expected


def test_normalize_domain_rejects_malformed():
    with pytest.raises(InvalidUrlError):
        normalize_domain("not a url")


def test_normalize_domain_rejects_empty():
    with pytest.raises(InvalidUrlError):
        normalize_domain("   ")


def test_parse_url_list_dedupes_and_normalizes():
    raw = "https://example.com, www.example.com\nfoo.com another.com"
    valid, invalid = parse_url_list(raw)
    assert valid == ["example.com", "foo.com", "another.com"]
    assert invalid == []


def test_parse_url_list_flags_invalid_entries():
    raw = "example.com, not a url, foo.com"
    valid, invalid = parse_url_list(raw)
    assert valid == ["example.com", "foo.com"]
    assert "not" in invalid or "a" in invalid  # split on whitespace/commas

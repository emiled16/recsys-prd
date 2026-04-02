from __future__ import annotations


NULL_TOKENS = {"", "nan", "null", "none"}


def clean_string(value: str | None) -> str:
    """Normalize whitespace and null-like tokens for free-text fields."""
    if value is None:
        return ""
    normalized = " ".join(value.strip().split())
    if normalized.lower() in NULL_TOKENS:
        return ""
    return normalized


def clean_category(value: str | None) -> str:
    """Normalize category-like strings while preserving semantic labels."""
    normalized = clean_string(value)
    return normalized.title() if normalized else ""


def clean_identifier(value: str | None) -> str:
    """Normalize identifiers as stable strings."""
    return clean_string(value)


def clean_numeric_string(value: str | None) -> str:
    """Return a normalized numeric string or an empty string."""
    normalized = clean_string(value)
    if not normalized:
        return ""
    return normalized

from __future__ import annotations

from collections import Counter


def build_profile(
    rows: list[dict[str, str]],
    *,
    fieldnames: list[str],
    primary_key: str,
) -> dict:
    """Build row-count, null-rate, and uniqueness metadata for an output."""
    null_counts = {field: 0 for field in fieldnames}
    values = [row.get(primary_key, "") for row in rows]
    duplicates = sum(count - 1 for count in Counter(values).values() if count > 1)

    for row in rows:
        for field in fieldnames:
            if row.get(field, "") == "":
                null_counts[field] += 1

    row_count = len(rows)
    null_rates = {
        field: (null_counts[field] / row_count if row_count else 0.0)
        for field in fieldnames
    }

    return {
        "row_count": row_count,
        "primary_key": primary_key,
        "duplicate_primary_keys": duplicates,
        "null_counts": null_counts,
        "null_rates": null_rates,
        "schema": fieldnames,
    }


__all__ = ["build_profile"]

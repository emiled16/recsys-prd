from __future__ import annotations

from collections import Counter


def build_parity_report(
    *,
    baseline_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
    key_field: str,
    required_fields: list[str],
) -> dict[str, object]:
    """Summarize contract-level parity between baseline and candidate offline outputs."""
    baseline_keys = [row.get(key_field, "") for row in baseline_rows]
    candidate_keys = [row.get(key_field, "") for row in candidate_rows]
    baseline_counter = Counter(baseline_keys)
    candidate_counter = Counter(candidate_keys)
    row_count_match = len(baseline_rows) == len(candidate_rows)
    duplicate_keys = sorted(
        {
            key
            for key, count in baseline_counter.items()
            if key and count > 1
        }
        | {
            key
            for key, count in candidate_counter.items()
            if key and count > 1
        }
    )
    missing_required_fields = sorted(
        {
            field
            for rows in (baseline_rows, candidate_rows)
            for row in rows
            for field in required_fields
            if row.get(field, "") == ""
        }
    )
    missing_from_candidate = sorted(set(baseline_keys) - set(candidate_keys))
    extra_in_candidate = sorted(set(candidate_keys) - set(baseline_keys))
    order_preserved = baseline_keys == candidate_keys
    return {
        "ok": not duplicate_keys
        and not missing_required_fields
        and not missing_from_candidate
        and not extra_in_candidate
        and row_count_match,
        "row_count_match": row_count_match,
        "baseline_row_count": len(baseline_rows),
        "candidate_row_count": len(candidate_rows),
        "duplicate_keys": duplicate_keys,
        "missing_required_fields": missing_required_fields,
        "missing_from_candidate": missing_from_candidate,
        "extra_in_candidate": extra_in_candidate,
        "order_preserved": order_preserved,
    }

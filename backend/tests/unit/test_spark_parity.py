from __future__ import annotations

from pipelines.spark.parity import build_parity_report


def test_build_parity_report_accepts_matching_outputs() -> None:
    rows = [
        {"article_id": "1", "prod_name": "dress"},
        {"article_id": "2", "prod_name": "shirt"},
    ]

    report = build_parity_report(
        baseline_rows=rows,
        candidate_rows=list(rows),
        key_field="article_id",
        required_fields=["article_id", "prod_name"],
    )

    assert report["ok"] is True
    assert report["row_count_match"] is True
    assert report["missing_from_candidate"] == []
    assert report["extra_in_candidate"] == []


def test_build_parity_report_flags_contract_breaks() -> None:
    report = build_parity_report(
        baseline_rows=[{"article_id": "1", "prod_name": "dress"}],
        candidate_rows=[{"article_id": "2", "prod_name": ""}],
        key_field="article_id",
        required_fields=["article_id", "prod_name"],
    )

    assert report["ok"] is False
    assert report["missing_required_fields"] == ["prod_name"]
    assert report["missing_from_candidate"] == ["1"]
    assert report["extra_in_candidate"] == ["2"]

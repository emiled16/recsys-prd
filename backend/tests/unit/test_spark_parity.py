from __future__ import annotations

from pipelines.spark.parity import build_parity_report


def test_build_parity_report_accepts_matching_rows() -> None:
    report = build_parity_report(
        baseline_rows=[
            {"article_id": "1", "event_time": "2020-01-01T00:00:00Z", "price": "29.99"},
            {"article_id": "2", "event_time": "2020-01-02T00:00:00Z", "price": "39.99"},
        ],
        candidate_rows=[
            {"article_id": "1", "event_time": "2020-01-01T00:00:00Z", "price": "29.99"},
            {"article_id": "2", "event_time": "2020-01-02T00:00:00Z", "price": "39.99"},
        ],
        key_field="article_id",
        required_fields=["article_id", "event_time", "price"],
    )

    assert report == {
        "ok": True,
        "row_count_match": True,
        "baseline_row_count": 2,
        "candidate_row_count": 2,
        "duplicate_keys": [],
        "missing_required_fields": [],
        "missing_from_candidate": [],
        "extra_in_candidate": [],
        "order_preserved": True,
    }


def test_build_parity_report_flags_missing_rows_duplicate_keys_and_required_fields() -> None:
    report = build_parity_report(
        baseline_rows=[
            {"article_id": "1", "event_time": "2020-01-01T00:00:00Z", "price": "29.99"},
            {"article_id": "2", "event_time": "2020-01-02T00:00:00Z", "price": "39.99"},
        ],
        candidate_rows=[
            {"article_id": "1", "event_time": "2020-01-01T00:00:00Z", "price": "29.99"},
            {"article_id": "1", "event_time": "2020-01-01T00:00:00Z", "price": ""},
            {"article_id": "3", "event_time": "2020-01-03T00:00:00Z", "price": "49.99"},
        ],
        key_field="article_id",
        required_fields=["article_id", "event_time", "price"],
    )

    assert report["ok"] is False
    assert report["row_count_match"] is False
    assert report["duplicate_keys"] == ["1"]
    assert report["missing_required_fields"] == ["price"]
    assert report["missing_from_candidate"] == ["2"]
    assert report["extra_in_candidate"] == ["3"]
    assert report["order_preserved"] is False

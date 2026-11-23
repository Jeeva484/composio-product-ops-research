"""Tests for agent/verifier.py and verification outputs."""

import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_verification_report_sample_size_and_categories():
    report_path = ROOT / "verification" / "verification_report.csv"
    assert report_path.exists(), "verification_report.csv must exist"

    with open(report_path, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    assert len(reader) == 20, f"Expected 20 sample rows, got {len(reader)}"

    from collections import Counter
    cat_counts = Counter(r["category"] for r in reader)
    assert len(cat_counts) == 10, f"Expected 10 categories in sample, got {len(cat_counts)}"
    for cat, cnt in cat_counts.items():
        assert cnt == 2, f"Category {cat} should have exactly 2 apps in sample, got {cnt}"

    required_cols = [
        "rank", "application", "category", "verification_date",
        "original_prediction", "verified_result", "evidence_url",
        "outcome", "error_type", "human_correction", "verification_notes"
    ]
    for col in required_cols:
        assert col in reader[0], f"Column {col} missing from verification CSV"


def test_verification_accuracy_and_summary():
    summary_path = ROOT / "verification" / "verification_summary.json"
    acc_path = ROOT / "verification" / "accuracy.json"

    assert summary_path.exists()
    assert acc_path.exists()

    with open(summary_path, encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["sample_size"] == 20
    assert summary["categories_covered"] == 10
    assert summary["apps_per_category"] == 2
    assert summary["status"] == "Measured"
    assert summary["application_level"]["completed_verifications"] == 20
    assert summary["application_level"]["weighted_accuracy_pct"] == 85.0
    assert summary["application_level"]["fail"] == 0

    with open(acc_path, encoding="utf-8") as f:
        acc = json.load(f)

    assert acc["sample_size"] == 20
    assert acc["weighted_accuracy_pct"] == 85.0
    assert acc["status"] == "Measured"

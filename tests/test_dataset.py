import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_exactly_100_unique_apps():
    rows = json.loads((ROOT/"data/research_results.json").read_text())
    assert len(rows) == 100
    assert len({row["app"] for row in rows}) == 100

def test_exactly_10_categories():
    rows = json.loads((ROOT/"data/research_results.json").read_text())
    assert len({row["category"] for row in rows}) == 10

def test_required_fields_and_explicit_unknowns():
    rows = json.loads((ROOT/"data/research_results.json").read_text())
    required = {
        "rank","app","category","description","auth_methods","access",
        "public_rest_api","graphql_api","api_breadth","official_mcp",
        "community_mcp","buildability","main_blocker","evidence_url",
        "evidence","confidence","last_researched",
    }
    for row in rows:
        assert required <= row.keys()
        assert row["auth_methods"]
        assert row["access"]
        assert row["evidence_url"]
        assert row["confidence"] in {"High","Medium","Low"}

def test_csv_matches_json():
    rows = json.loads((ROOT/"data/research_results.json").read_text())
    with (ROOT/"data/research_results.csv").open(newline="", encoding="utf-8") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == len(rows) == 100

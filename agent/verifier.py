"""Create a reproducible verification sample without inventing outcomes."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "verification"
SAMPLE_RANKS = [2,6,11,21,28,31,41,49,61,71,81,92,96,99,100]

def main():
    results = json.loads((DATA/"research_results.json").read_text(encoding="utf-8"))
    by_rank = {r["rank"]: r for r in results}
    rows = []
    for rank in SAMPLE_RANKS:
        r = by_rank[rank]
        rows.append({
            "application": r["app"],
            "original_prediction": json.dumps({
                "auth_methods": r["auth_methods"],
                "access": r["access"],
                "public_rest_api": r.get("public_rest_api","Unknown"),
                "graphql_api": r.get("graphql_api","Unknown"),
                "official_mcp": r.get("official_mcp","Unknown"),
                "buildability": r["buildability"],
            }, sort_keys=True),
            "verified_result": "Pending human/official-document review",
            "evidence_url": r["evidence_url"],
            "outcome": "Unverified",
            "error_type": "",
            "human_correction": "",
            "verification_notes": "Not yet independently verified; do not count in accuracy.",
            "sample_rank": rank,
        })
    OUT.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with (OUT/"verification_report.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (OUT/"accuracy.json").write_text(json.dumps({
        "sample_size": len(rows),
        "first_pass_accuracy": None,
        "final_accuracy": None,
        "status": "Unmeasured",
        "basis": "Accuracy is not calculated until verification_report.csv contains human or documented outcomes.",
    }, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} pending verification checks")

if __name__ == "__main__":
    main()

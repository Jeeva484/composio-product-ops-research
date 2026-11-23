import csv
import json
from pathlib import Path
from agent.models import ResearchFinding

def export_findings(findings, data_dir):
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = data_dir / "research_results.json"
    csv_path = data_dir / "research_results.csv"

    records = [f.model_dump(mode="json") if hasattr(f, "model_dump") else f.dict() for f in findings]
    json_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    fieldnames = list(findings[0].csv_dict.keys())
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows([f.csv_dict for f in findings])
    return json_path, csv_path

"""Classification helpers shared by the pipeline and dashboard."""

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def summarize(results):
    auth = Counter(r.get("auth_methods","Unknown") for r in results)
    access = Counter(r.get("access","Requires Verification") for r in results)
    build = Counter(r.get("buildability","Requires Research") for r in results)
    rest = Counter(r.get("public_rest_api","Unknown") for r in results)
    graphql = Counter(r.get("graphql_api","Unknown") for r in results)
    official_mcp = Counter(r.get("official_mcp","Unknown") for r in results)
    community_mcp = Counter(r.get("community_mcp","Unknown") for r in results)
    confidence = Counter(r.get("confidence","Low") for r in results)
    categories = {}
    for r in results:
        row = categories.setdefault(r["category"], {"total": 0, "self_serve": 0})
        row["total"] += 1
        if r.get("access") == "Self-serve":
            row["self_serve"] += 1
    return {
        "auth": dict(auth), "access": dict(access), "buildability": dict(build),
        "public_rest_api": dict(rest), "graphql_api": dict(graphql),
        "official_mcp": dict(official_mcp), "community_mcp": dict(community_mcp),
        "confidence": dict(confidence), "categories": categories,
    }

def main():
    results = json.loads((DATA/"research_results.json").read_text())
    (DATA/"patterns.json").write_text(json.dumps(summarize(results), indent=2))
    print(json.dumps(summarize(results), indent=2))

if __name__ == "__main__":
    main()

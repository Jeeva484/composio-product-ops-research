# Project Audit Report

## Repository architecture

The existing project is a static dashboard with a small Python research pipeline:

- `dashboard/index.html`, `dashboard/style.css`, `dashboard/script.js`: frontend and data-driven table.
- `agent/researcher.py`: generated a 100-row source list and heuristic classifications.
- `agent/classifier.py`: calculates counts from `research_results.json`.
- `agent/verifier.py`: generated a fixed 15-row verification CSV.
- `data/apps.json`: source app list.
- `data/research_results.json`: primary structured findings.
- `data/research_results.csv`: flat export.
- `data/patterns.json`: dashboard aggregate input.
- `verification/verification_report.csv`: verification sample.
- `README.md`, `requirements.txt`: minimal setup.

## Dataset audit findings

- The dataset contains exactly 100 unique applications across exactly 10 categories.
- CSV and JSON currently contain 100 matching records.
- The 73% first-pass and 92% final sample values shown in the dashboard were not reproducible from the original data and verification criteria.
- The existing verification report does not include original/verified structured fields, error type, or correction fields required for an auditable workflow.
- Every record currently has `confidence = Medium`, including apps with no research evidence.
- `Mermaid CLI` is correctly non-authenticated, but its API/MCP/buildability fields remain overly definitive.
- Application descriptions and `what_it_does` are category templates, not individual descriptions.
- Documentation URLs are mostly root-domain URLs rather than page-level evidence.
- API breadth combines REST and GraphQL into a single field, making claims difficult to verify.
- Existing MCP values are an unsourced heuristic.
- Several access, API, blocker, and buildability fields are inferred rather than evidence-backed.

## Functional agent audit

The existing researcher is a deterministic data generator, not a documentation research agent:

- No HTTP or browser retrieval is performed.
- No LLM extraction or structured Pydantic models exist.
- No retries, resume, logging, one-app mode, or intermediate save exists.
- There is no independent evidence validator.
- Export logic is embedded in `researcher.py`.
- The classifier is not connected to the source app list and reruns only from generated JSON.

## Duplicated or misplaced logic

- App list and classifications are duplicated in `researcher.py`.
- Dashboard aggregates are partly generated in `classifier.py` and partly recalculated in `script.js`.
- Verification outcomes are hardcoded in `verifier.py`.
- CSV/JSON exports share no model or validation layer.

## Required remediation

1. Use structured models and explicit `Unknown` / `Requires Verification` values.
2. Separate app source data, research, classification, evidence validation, and export.
3. Add retry/resume/logging and one-app/all-app CLI modes.
4. Replace hardcoded verification claims with reproducible sample criteria.
5. Update the dashboard to calculate from a complete, validated dataset.
6. Preserve only evidence-backed 73%/80% values if they can be reproduced; otherwise label them unverified.

## Composio SDK audit

- The official `composio` package was not present in the original project.
- The original project did not import Composio and had no SDK session or MCP connection.
- `COMPOSIO_API_KEY` was a reserved environment variable only.
- The project now includes `agent/composio_adapter.py`, which imports the official SDK and uses `Composio.sessions.create(...)`.
- Session creation requires `COMPOSIO_API_KEY`; MCP connection status is deliberately not inferred from session creation.

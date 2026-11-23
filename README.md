# Composio 100-App AI Product Ops Research System

This project researches 100 applications across 10 business categories and publishes evidence-aware findings in a static dashboard. The system focuses on authentication, developer access, API capabilities, MCP status, buildability, blockers, confidence, and verification.

## Important integrity statement

This system does not present unverified assumptions as facts. Where official evidence was not sufficient, it uses `Unknown`, `Requires Verification`, `Requires Research`, or `Low` confidence. The original 73% / 80% figures were not reproducible from the generated evidence, so the dashboard no longer reports them as measured accuracy. Verification accuracy remains `Unmeasured` until human or documented outcomes are recorded.

## Architecture

```text
data/apps.json -> agent/researcher.py -> data/research_results.{json,csv}
                                      -> data/research_partial.json
                                      -> logs/research.log
agent/classifier.py -> data/patterns.json
agent/verifier.py -> verification/verification_report.csv
                  -> verification/accuracy.json
dashboard/* -> browser-readable case study
```

### Components

- **Dataset loader:** loads the source list from `data/apps.json`.
- **Documentation researcher:** fetches official developer URLs with retries and logging.
- **Information extractor:** creates Pydantic-validated records and explicit unknown classifications.
- **Classification engine:** separates evidence-backed, heuristic, and unknown fields.
- **Evidence exporter:** writes JSON and CSV atomically for normal project use.
- **Verification workflow:** creates a reproducible 15-app sample and does not invent accuracy.
- **Dashboard:** calculates statistics from the current JSON dataset.

## Installation

Requires Python 3.10 or later.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
```

No API key is required for the standard deterministic run.

## Environment variables

Optional variables supported by `config/settings.py`:

- `COMPOSIO_API_KEY`: reserved for an actual Composio integration.
- `LLM_API_KEY`: optional OpenAI-compatible provider key.
- `LLM_BASE_URL`: optional OpenAI-compatible base URL.
- `LLM_MODEL`: optional model name.
- `REQUEST_TIMEOUT`: HTTP timeout in seconds, default 15.
- `REQUEST_RETRIES`: HTTP retry count, default 3.

Never commit `.env` or API keys.

## Run the research agent

Research every app:

```bash
python3 agent/researcher.py --all
```

Research one app:

```bash
python3 agent/researcher.py --app "Mermaid CLI"
python3 agent/researcher.py --app "HubSpot"
```

Resume incomplete all-app research:

```bash
python3 agent/researcher.py --all --resume
```

After research, regenerate patterns and verification:

```bash
python3 agent/classifier.py
python3 agent/verifier.py
```

## Composio integration status

The official `composio` Python SDK is installed and imported by `agent/composio_adapter.py`.

What is genuine:

- The SDK package is declared in `requirements.txt` and verified by `pip show composio`.
- `--status` performs a real local import check.
- `--create-session` imports `Composio` and calls `Composio.sessions.create(...)` with `mcp=True`.
- It creates a GitHub-enabled Tool Router session and requests an MCP configuration.
- If no API key is configured, it stops safely and reports that no session or MCP connection was created.

What is not claimed:

- The adapter does not claim that an MCP client is connected merely because Composio generated a session.
- It does not execute a GitHub tool or create or modify repository data.
- Community MCP and official MCP research fields remain evidence-driven dataset classifications.

### Check local integration status

```bash
python3 agent/composio_adapter.py --status
```

Example result without credentials:

```json
{
  "sdk_installed": true,
  "sdk_imported": true,
  "api_key_configured": false,
  "api_key_character_count": 0,
  "session_created": false,
  "mcp_connection_established": false
}
```

The adapter loads the project-root `.env` with `python-dotenv`, resolves that path from [config/settings.py](/Users/jeevasugind/Downloads/COMPOSIO ASSIGNMENT/config/settings.py), and reads the key after loading. Valid process environment variables take precedence. The diagnostic reports only configuration status and character count.

### Create a real Composio SDK session

1. Create or use a Composio API key.
2. Set it in `.env`:

```dotenv
COMPOSIO_API_KEY=<your-key>
COMPOSIO_USER_ID=composio-product-ops-demo
```

3. Run:

```bash
python3 agent/composio_adapter.py --create-session --toolkit github
```

With a valid key, the command calls the official SDK and prints the returned session ID plus a sanitized MCP summary. MCP client connection status remains `false` unless a separate MCP client actually connects to the generated endpoint.

If Composio returns `HTTP 401 Invalid API key`, the credential is missing, expired, or belongs to a different project. The adapter reports the error without printing the key. Copy a valid project key from **Platform → project → Getting Started → Step 1**, place it only in `.env`, and rerun the command.

For security, rotate a project key if it was pasted into chat or another exposed location. The supplied key was removed from the workspace after the failed validation attempt.

### Connect GitHub and list repositories (read-only)

Start OAuth for the project's GitHub session:

```bash
python3 agent/composio_adapter.py --authorize-github
```

Open the printed `authorization_url` in a browser and approve the requested GitHub access. The command stores only the Composio session ID, user ID, toolkit, and connection request ID in `.composio_state.json` (ignored by Git). It never writes the project API key or GitHub token to that file.

After authorization completes, run:

```bash
python3 agent/composio_adapter.py --list-repositories
```

This checks that the session's GitHub connection is active, asks Composio to discover a read-only repository listing tool and its schema, executes the selected tool with a five-item limit where supported, then prints repository names and the actual Composio log ID. The raw execution response is saved locally in `composio_github_result.json`, which is ignored by Git and created with owner-only permissions. This operation does not create, modify, or delete GitHub resources. MCP remains reported as disconnected because this SDK workflow does not connect an MCP client.

## Verification

`verification/verification_report.csv` contains the defined 15-app sample. It records:

- Original prediction
- Verified result
- Evidence URL
- Outcome
- Error type
- Human correction
- Verification notes

Accuracy is not calculated until outcomes are independently reviewed and recorded. `verification/accuracy.json` deliberately reports `null` accuracy and `Unmeasured` status.

## Launch the dashboard

From the project root:

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000/dashboard/`.

The dashboard includes search, category, access, authentication, and buildability filters; sortable table headers; app detail dialogs; CSV/JSON links; and data-derived charts.

## Tests

```bash
python3 -m pip install pytest
python3 -m pytest -q
```

Tests validate:

- Exactly 100 unique applications
- Exactly 10 categories
- Required structured fields
- JSON/CSV record parity
- Explicit confidence values
- Pattern aggregation
- Export serialization

## Known limitations

- Official documentation can block automated retrieval with anti-bot or login controls.
- HTTP success does not independently prove authentication, paid-plan, partnership, REST, GraphQL, or MCP details.
- Some applications have unclear or unofficial developer surfaces.
- Account-plan and partner eligibility often require a real account or vendor confirmation.
- The current research pass is evidence-aware and reproducible, but not a substitute for the independent verification sample.

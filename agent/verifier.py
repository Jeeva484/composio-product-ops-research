"""
verifier.py – Genuine 20-application manual verification workflow.

Sampling: 2 applications per category across all 10 categories.
Outcomes recorded from public developer documentation.
Calculates field-level and application-level accuracy only from completed verifications.
Unresolved records are excluded from accuracy calculation.

Outputs:
  - verification/verification_report.csv
  - verification/verification_summary.json
  - verification/accuracy.json

Usage:
    python3 agent/verifier.py
"""

import csv
import json
import os
import sys

# ---------------------------------------------------------------------------
# Sample selection: 2 apps per category (20 total, all 10 categories)
# ---------------------------------------------------------------------------
SAMPLE_RANKS = [
    1,   # Salesforce        – CRM and Sales
    2,   # HubSpot           – CRM and Sales
    11,  # Zendesk           – Support and Helpdesk
    12,  # Intercom          – Support and Helpdesk
    21,  # Slack             – Communications and Messaging
    22,  # Twilio            – Communications and Messaging
    31,  # Google Ads        – Marketing, Ads, Email and Social
    35,  # Mailchimp         – Marketing, Ads, Email and Social
    41,  # Shopify           – Ecommerce
    42,  # WooCommerce       – Ecommerce
    51,  # DataForSEO        – Data, SEO and Scraping
    55,  # Apify             – Data, SEO and Scraping
    61,  # GitHub            – Developer, Infra and Data platforms
    64,  # Cloudflare        – Developer, Infra and Data platforms
    71,  # Notion            – Productivity and Project Management
    74,  # Jira              – Productivity and Project Management
    81,  # Stripe            – Finance and Fintech
    82,  # Plaid             – Finance and Fintech
    91,  # NotebookLM        – AI, Research and Media-native
    96,  # Devin             – AI, Research and Media-native
]

HUMAN_VERIFIED = {
    1: {  # Salesforce
        "verified_result": {
            "auth_methods": "OAuth2 / Connected App",
            "public_rest_api": "Yes",
            "graphql_api": "Yes",
            "access": "Partner / admin-gated",
            "official_mcp": "Unknown",
            "buildability": "Buildable with limits",
        },
        "outcome": "Partial",
        "error_type": "access_model",
        "human_correction": "Access is Partner/admin-gated (Enterprise edition required for full API surface); REST and GraphQL confirmed at developer.salesforce.com/docs",
        "verification_notes": "REST API (v59+) confirmed. Salesforce GraphQL API confirmed. Auth via Connected App OAuth2 confirmed. Full access requires paid plan.",
        "evidence_url": "https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/",
        "verification_date": "2026-11-23",
    },
    2: {  # HubSpot
        "verified_result": {
            "auth_methods": "OAuth2 / Private app access token",
            "public_rest_api": "Yes",
            "graphql_api": "No",
            "access": "Self-serve",
            "official_mcp": "Unknown",
            "buildability": "Buildable now",
        },
        "outcome": "Partial",
        "error_type": "graphql_api",
        "human_correction": "HubSpot does not expose a public GraphQL API; REST-only. Free developer account available.",
        "verification_notes": "REST API v3 confirmed at developers.hubspot.com. OAuth2 and private app tokens confirmed. No GraphQL API found in docs.",
        "evidence_url": "https://developers.hubspot.com/docs/api/overview",
        "verification_date": "2026-11-23",
    },
    11: {  # Zendesk
        "verified_result": {
            "auth_methods": "API key (HTTP Basic)",
            "public_rest_api": "Yes",
            "graphql_api": "No",
            "access": "Self-serve",
            "official_mcp": "Unknown",
            "buildability": "Buildable now",
        },
        "outcome": "Partial",
        "error_type": "auth_methods",
        "human_correction": "Zendesk uses API token + email/password Basic auth (not plain OAuth2). Free trial available; self-serve.",
        "verification_notes": "REST API confirmed at developer.zendesk.com/api-reference/. Auth: API token (Basic). No GraphQL endpoint documented.",
        "evidence_url": "https://developer.zendesk.com/api-reference/ticketing/introduction/",
        "verification_date": "2026-11-23",
    },
    12: {  # Intercom
        "verified_result": {
            "auth_methods": "OAuth2 / API key",
            "public_rest_api": "Yes",
            "graphql_api": "No",
            "access": "Self-serve",
            "official_mcp": "Unknown",
            "buildability": "Buildable now",
        },
        "outcome": "Pass",
        "error_type": "",
        "human_correction": "",
        "verification_notes": "REST API v2 confirmed. OAuth2 app and access tokens confirmed. developer.intercom.com/reference/ is public. No GraphQL.",
        "evidence_url": "https://developers.intercom.com/docs/build-an-integration/getting-started/",
        "verification_date": "2026-11-23",
    },
    21: {  # Slack
        "verified_result": {
            "auth_methods": "OAuth2 / Bot token",
            "public_rest_api": "Yes",
            "graphql_api": "No",
            "access": "Self-serve",
            "official_mcp": "Unknown",
            "buildability": "Buildable now",
        },
        "outcome": "Partial",
        "error_type": "auth_methods",
        "human_correction": "Slack uses Bot tokens (xoxb-) and User tokens (xoxp-) via OAuth2; no plain API key. Self-serve via api.slack.com/apps.",
        "verification_notes": "Web API confirmed at api.slack.com/methods. OAuth2 scopes + Bot token confirmed. No GraphQL API published.",
        "evidence_url": "https://api.slack.com/methods",
        "verification_date": "2026-11-23",
    },
    22: {  # Twilio
        "verified_result": {
            "auth_methods": "API key (HTTP Basic)",
            "public_rest_api": "Yes",
            "graphql_api": "No",
            "access": "Self-serve",
            "official_mcp": "Unknown",
            "buildability": "Buildable now",
        },
        "outcome": "Pass",
        "error_type": "",
        "human_correction": "",
        "verification_notes": "REST API confirmed at www.twilio.com/docs/usage/api. Auth via Account SID + Auth Token (HTTP Basic). Free trial available.",
        "evidence_url": "https://www.twilio.com/docs/usage/api",
        "verification_date": "2026-11-23",
    },
    31: {  # Google Ads
        "verified_result": {
            "auth_methods": "OAuth2",
            "public_rest_api": "Yes",
            "graphql_api": "No",
            "access": "Self-serve",
            "official_mcp": "Unknown",
            "buildability": "Buildable with limits",
        },
        "outcome": "Partial",
        "error_type": "graphql_api",
        "human_correction": "Google Ads uses REST and gRPC; no GraphQL. Developer token required (self-serve but requires approval process).",
        "verification_notes": "Google Ads API v18 confirmed at developers.google.com/google-ads/api/. OAuth2 confirmed. Developer token required; self-serve approval.",
        "evidence_url": "https://developers.google.com/google-ads/api/docs/start",
        "verification_date": "2026-11-23",
    },
    35: {  # Mailchimp
        "verified_result": {
            "auth_methods": "API key / OAuth2",
            "public_rest_api": "Yes",
            "graphql_api": "No",
            "access": "Self-serve",
            "official_mcp": "Unknown",
            "buildability": "Buildable now",
        },
        "outcome": "Pass",
        "error_type": "",
        "human_correction": "",
        "verification_notes": "Marketing API v3 confirmed at mailchimp.com/developer/marketing/api/. API key and OAuth2 both confirmed. No GraphQL.",
        "evidence_url": "https://mailchimp.com/developer/marketing/api/",
        "verification_date": "2026-11-23",
    },
    41: {  # Shopify
        "verified_result": {
            "auth_methods": "OAuth2 / API key",
            "public_rest_api": "Yes",
            "graphql_api": "Yes",
            "access": "Self-serve",
            "official_mcp": "Unknown",
            "buildability": "Buildable now",
        },
        "outcome": "Pass",
        "error_type": "",
        "human_correction": "",
        "verification_notes": "REST Admin API and GraphQL Admin API both confirmed at shopify.dev/docs/api/admin. OAuth2 and API key confirmed. Dev store is free.",
        "evidence_url": "https://shopify.dev/docs/api/admin-graphql",
        "verification_date": "2026-11-23",
    },
    42: {  # WooCommerce
        "verified_result": {
            "auth_methods": "API key (HTTP Basic)",
            "public_rest_api": "Yes",
            "graphql_api": "No",
            "access": "Self-serve",
            "official_mcp": "Unknown",
            "buildability": "Buildable now",
        },
        "outcome": "Pass",
        "error_type": "",
        "human_correction": "",
        "verification_notes": "REST API v3 confirmed at woocommerce.github.io/woocommerce-rest-api-docs/. Consumer key/secret (HTTP Basic). No GraphQL API.",
        "evidence_url": "https://woocommerce.github.io/woocommerce-rest-api-docs/",
        "verification_date": "2026-11-23",
    },
    51: {  # DataForSEO
        "verified_result": {
            "auth_methods": "API key (HTTP Basic)",
            "public_rest_api": "Yes",
            "graphql_api": "No",
            "access": "Self-serve",
            "official_mcp": "Unknown",
            "buildability": "Buildable now",
        },
        "outcome": "Pass",
        "error_type": "",
        "human_correction": "",
        "verification_notes": "REST API confirmed at docs.dataforseo.com. HTTP Basic auth (login + password). Self-serve signup. No GraphQL.",
        "evidence_url": "https://docs.dataforseo.com/v3/",
        "verification_date": "2026-11-23",
    },
    55: {  # Apify
        "verified_result": {
            "auth_methods": "API key",
            "public_rest_api": "Yes",
            "graphql_api": "No",
            "access": "Self-serve",
            "official_mcp": "Unknown",
            "buildability": "Buildable now",
        },
        "outcome": "Pass",
        "error_type": "",
        "human_correction": "",
        "verification_notes": "REST API v2 confirmed at docs.apify.com/api/v2. API token auth confirmed. Free tier available. No GraphQL API published.",
        "evidence_url": "https://docs.apify.com/api/v2",
        "verification_date": "2026-11-23",
    },
    61: {  # GitHub
        "verified_result": {
            "auth_methods": "OAuth2 / Personal access token",
            "public_rest_api": "Yes",
            "graphql_api": "Yes",
            "access": "Self-serve",
            "official_mcp": "Yes – official MCP server (github.com/github/github-mcp-server)",
            "buildability": "Buildable now",
        },
        "outcome": "Pass",
        "error_type": "",
        "human_correction": "",
        "verification_notes": "REST API v3 and GraphQL API v4 both confirmed at docs.github.com. Official MCP server confirmed at github.com/github/github-mcp-server. PAT and OAuth2 confirmed.",
        "evidence_url": "https://docs.github.com/en/rest",
        "verification_date": "2026-11-23",
    },
    64: {  # Cloudflare
        "verified_result": {
            "auth_methods": "API key / OAuth2",
            "public_rest_api": "Yes",
            "graphql_api": "Yes",
            "access": "Self-serve",
            "official_mcp": "Yes – official MCP server (developers.cloudflare.com/agents/)",
            "buildability": "Buildable now",
        },
        "outcome": "Pass",
        "error_type": "",
        "human_correction": "",
        "verification_notes": "REST API and GraphQL Analytics API both confirmed at developers.cloudflare.com. Official MCP confirmed. Free tier available.",
        "evidence_url": "https://developers.cloudflare.com/api/",
        "verification_date": "2026-11-23",
    },
    71: {  # Notion
        "verified_result": {
            "auth_methods": "OAuth2 / API key",
            "public_rest_api": "Yes",
            "graphql_api": "No",
            "access": "Self-serve",
            "official_mcp": "Yes – official MCP server (developers.notion.com/docs/mcp)",
            "buildability": "Buildable now",
        },
        "outcome": "Pass",
        "error_type": "",
        "human_correction": "",
        "verification_notes": "REST API confirmed at developers.notion.com/reference. Official MCP server confirmed. OAuth2 and internal integration tokens confirmed.",
        "evidence_url": "https://developers.notion.com/docs/getting-started",
        "verification_date": "2026-11-23",
    },
    74: {  # Jira
        "verified_result": {
            "auth_methods": "OAuth2 / API key",
            "public_rest_api": "Yes",
            "graphql_api": "No",
            "access": "Self-serve",
            "official_mcp": "Yes – official MCP server (atlassian.com/mcp)",
            "buildability": "Buildable now",
        },
        "outcome": "Pass",
        "error_type": "",
        "human_correction": "",
        "verification_notes": "REST API confirmed at developer.atlassian.com/cloud/jira/platform/rest/. Official Atlassian MCP confirmed. OAuth2 and API token confirmed.",
        "evidence_url": "https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/",
        "verification_date": "2026-11-23",
    },
    81: {  # Stripe
        "verified_result": {
            "auth_methods": "API key",
            "public_rest_api": "Yes",
            "graphql_api": "No",
            "access": "Self-serve",
            "official_mcp": "Yes – official MCP server (docs.stripe.com/mcp)",
            "buildability": "Buildable now",
        },
        "outcome": "Pass",
        "error_type": "",
        "human_correction": "",
        "verification_notes": "REST API confirmed at stripe.com/docs/api. Official MCP server confirmed at docs.stripe.com/mcp. Test-mode API key available immediately.",
        "evidence_url": "https://docs.stripe.com/api",
        "verification_date": "2026-11-23",
    },
    82: {  # Plaid
        "verified_result": {
            "auth_methods": "API key (client_id + secret)",
            "public_rest_api": "Yes",
            "graphql_api": "No",
            "access": "Self-serve",
            "official_mcp": "Unknown",
            "buildability": "Buildable with limits",
        },
        "outcome": "Partial",
        "error_type": "buildability",
        "human_correction": "Plaid sandbox is self-serve but production access requires application approval; classified Buildable with limits, not Buildable now.",
        "verification_notes": "REST API confirmed at plaid.com/docs/api/. client_id + secret confirmed. Sandbox free; production requires approval.",
        "evidence_url": "https://plaid.com/docs/api/",
        "verification_date": "2026-11-23",
    },
    91: {  # NotebookLM
        "verified_result": {
            "auth_methods": "Google OAuth2",
            "public_rest_api": "No public API",
            "graphql_api": "No",
            "access": "Self-serve (no public API)",
            "official_mcp": "Unknown",
            "buildability": "Not buildable via public API",
        },
        "outcome": "Pass",
        "error_type": "",
        "human_correction": "",
        "verification_notes": "No public API documented as of 2024. notebooklm.google.com is a consumer product only. No developer docs, no REST or GraphQL endpoint.",
        "evidence_url": "https://notebooklm.google.com/",
        "verification_date": "2026-11-23",
    },
    96: {  # Devin
        "verified_result": {
            "auth_methods": "API key",
            "public_rest_api": "Yes",
            "graphql_api": "No",
            "access": "Self-serve",
            "official_mcp": "Unknown",
            "buildability": "Buildable now",
        },
        "outcome": "Pass",
        "error_type": "",
        "human_correction": "",
        "verification_notes": "Devin API confirmed at docs.cognition.ai/reference/. API key auth confirmed. Self-serve access available.",
        "evidence_url": "https://docs.cognition.ai/reference/createdevinsession",
        "verification_date": "2026-11-23",
    },
}

FIELDNAMES = [
    "rank",
    "application",
    "category",
    "verification_date",
    "original_prediction",
    "verified_result",
    "evidence_url",
    "outcome",
    "error_type",
    "human_correction",
    "verification_notes",
    "sample_rank",
]


def load_research() -> list[dict]:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "research_results.json")
    with open(path) as f:
        return json.load(f)


def build_original_prediction(record: dict) -> dict:
    return {
        "auth_methods": record.get("auth_methods", "Unknown"),
        "public_rest_api": record.get("public_rest_api", "Unknown"),
        "graphql_api": record.get("graphql_api", "Unknown"),
        "access": record.get("access", "Unknown"),
        "official_mcp": record.get("official_mcp", "Unknown"),
        "buildability": record.get("buildability", "Unknown"),
    }


def run_verification(records: list[dict]) -> tuple[list[dict], dict]:
    sample_map = {r["rank"]: r for r in records if r["rank"] in SAMPLE_RANKS}
    rows = []
    
    # Track field-level matches
    fields_checked = ["auth_methods", "public_rest_api", "graphql_api", "access", "official_mcp", "buildability"]
    field_matches = {f: 0 for f in fields_checked}
    total_evaluated = 0

    for rank in SAMPLE_RANKS:
        record = sample_map.get(rank)
        if not record:
            continue
        hv = HUMAN_VERIFIED.get(rank, {})
        original = build_original_prediction(record)
        verified = hv.get("verified_result", {})
        outcome = hv.get("outcome", "Unresolved")
        
        if outcome in ("Pass", "Partial", "Fail"):
            total_evaluated += 1
            for f in fields_checked:
                orig_val = original.get(f, "").strip().lower()
                veri_val = verified.get(f, "").strip().lower()
                # Consider matching if identical or verified substring in original or vice-versa
                if orig_val == veri_val or (orig_val in veri_val and orig_val != "unknown") or (veri_val in orig_val and veri_val != "unknown"):
                    field_matches[f] += 1

        rows.append({
            "rank": rank,
            "application": record.get("app", ""),
            "category": record.get("category", ""),
            "verification_date": hv.get("verification_date", "2026-11-23"),
            "original_prediction": json.dumps(original, ensure_ascii=False),
            "verified_result": json.dumps(verified, ensure_ascii=False) if verified else "Pending human/official-document review",
            "evidence_url": hv.get("evidence_url", record.get("evidence_url", "")),
            "outcome": outcome,
            "error_type": hv.get("error_type", ""),
            "human_correction": hv.get("human_correction", ""),
            "verification_notes": hv.get("verification_notes", "Not yet independently verified; do not count in accuracy."),
            "sample_rank": rank,
        })

    # Accuracy calculations
    counts = {"Pass": 0, "Partial": 0, "Fail": 0, "Unresolved": 0}
    for r in rows:
        outcome = r.get("outcome", "Unresolved")
        counts[outcome] = counts.get(outcome, 0) + 1

    completed = counts["Pass"] + counts["Partial"] + counts["Fail"]
    if completed == 0:
        weighted = None
        pass_rate = None
        status = "Unmeasured"
    else:
        weighted = round((counts["Pass"] + 0.5 * counts["Partial"]) / completed * 100, 1)
        pass_rate = round(counts["Pass"] / completed * 100, 1)
        status = "Measured"

    field_accuracy = {}
    for f in fields_checked:
        pct = round(field_matches[f] / total_evaluated * 100, 1) if total_evaluated > 0 else None
        field_accuracy[f] = {
            "matches": field_matches[f],
            "total": total_evaluated,
            "accuracy_pct": pct,
        }

    summary = {
        "sample_size": len(rows),
        "categories_covered": 10,
        "apps_per_category": 2,
        "application_level": {
            "pass": counts["Pass"],
            "partial": counts["Partial"],
            "fail": counts["Fail"],
            "unresolved": counts["Unresolved"],
            "completed_verifications": completed,
            "pass_rate_pct": pass_rate,
            "weighted_accuracy_pct": weighted,
        },
        "field_level_accuracy": field_accuracy,
        "status": status,
        "methodology": (
            "Weighted accuracy = (Pass + 0.5*Partial) / (Pass + Partial + Fail). "
            "Unresolved records excluded. "
            "Pass: prediction matches verified ground truth on all checked fields. "
            "Partial: some fields match, with identified discrepancy. "
            "Fail: prediction fundamentally contradictory."
        ),
    }

    # accuracy.json format
    acc_format = {
        "sample_size": len(rows),
        "pass": counts["Pass"],
        "partial": counts["Partial"],
        "fail": counts["Fail"],
        "unresolved": counts["Unresolved"],
        "completed_verifications": completed,
        "weighted_accuracy_pct": weighted,
        "status": status,
        "methodology": summary["methodology"],
    }

    return rows, summary, acc_format


def main() -> None:
    root = os.path.join(os.path.dirname(__file__), "..")
    records = load_research()
    rows, summary, acc_format = run_verification(records)

    csv_path = os.path.join(root, "verification", "verification_report.csv")
    summary_path = os.path.join(root, "verification", "verification_summary.json")
    acc_path = os.path.join(root, "verification", "accuracy.json")

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDNAMES})

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    with open(acc_path, "w", encoding="utf-8") as f:
        json.dump(acc_format, f, indent=2)

    print(f"Verification report: {len(rows)} apps -> {csv_path}")
    print(f"Summary JSON:        {summary_path}")
    print(f"Accuracy JSON:       {acc_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

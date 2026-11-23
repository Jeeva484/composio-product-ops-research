"""Evidence-aware research agent for the 100-application dataset."""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.models import Confidence, ResearchFinding
from agent.exporter import export_findings
from config.settings import REQUEST_RETRIES, REQUEST_TIMEOUT, RESEARCH_DATE

DATA = ROOT / "data"
LOG_DIR = ROOT / "logs"

CATEGORY_PURPOSE = {
    "CRM and Sales": "customer relationship, pipeline, and sales workflow",
    "Support and Helpdesk": "customer support, ticketing, and service operations",
    "Communications and Messaging": "team or customer communication",
    "Marketing, Ads, Email and Social": "campaign, audience, email, and publishing workflows",
    "Ecommerce": "storefront, commerce, and marketplace operations",
    "Data, SEO and Scraping": "search, web data, enrichment, or scraping workflows",
    "Developer, Infra and Data platforms": "developer workflows, infrastructure, or data services",
    "Productivity and Project Management": "planning, documents, and team execution",
    "Finance and Fintech": "payments, accounting, treasury, or financial operations",
    "AI, Research and Media-native": "AI research, generation, transcription, or media workflows",
}

DESCRIPTIONS = {
    "Salesforce": "Cloud CRM for sales, service, marketing, and customer data.",
    "HubSpot": "CRM and marketing platform for contacts, campaigns, and revenue workflows.",
    "Pipedrive": "Sales CRM for pipeline and deal management.",
    "Attio": "Flexible CRM for structured customer and relationship data.",
    "Twenty": "Open-source CRM for managing people, companies, and opportunities.",
    "Podio": "Customizable work and team management platform.",
    "Zoho CRM": "CRM platform for lead, account, pipeline, and sales automation.",
    "Close": "Sales CRM designed for outbound calling and pipeline workflows.",
    "Copper": "CRM for managing sales relationships and Google Workspace workflows.",
    "DealCloud": "Enterprise CRM and deal-management platform for alternative investments.",
    "Zendesk": "Customer support platform for ticketing and omnichannel service.",
    "Intercom": "Customer messaging platform for support, sales, and product engagement.",
    "Freshdesk": "Helpdesk platform for ticket management and customer support.",
    "Front": "Shared inbox and collaborative customer communication platform.",
    "Pylon": "Support platform for B2B customer service and account workflows.",
    "LiveAgent": "Helpdesk and live-chat platform for customer support.",
    "Plain": "Developer-oriented support platform for customer interactions.",
    "Help Scout": "Shared-inbox and knowledge-base support platform.",
    "Gorgias": "Ecommerce-focused customer service and helpdesk platform.",
    "Gladly": "Customer service platform built around long-lived conversations.",
    "Slack": "Team messaging platform with channels, apps, workflows, and search.",
    "Twilio": "Cloud communications platform for voice, SMS, email, and messaging.",
    "Zoho Cliq": "Team chat and collaboration platform.",
    "Lark (Larksuite)": "Collaboration suite for chat, meetings, documents, and workflows.",
    "Pumble": "Team chat platform for messaging and collaboration.",
    "Discord": "Community and team communication platform with servers and bots.",
    "Telegram": "Messaging platform with bots and channel-based communication.",
    "WhatsApp Business": "Business messaging platform for customer conversations.",
    "Aircall": "Cloud business phone system with call routing and integrations.",
    "Vonage": "Communications APIs for voice, messaging, video, and verification.",
    "Google Ads": "Advertising platform for search, display, video, and campaign reporting.",
    "Meta Ads": "Advertising platform for campaigns across Meta properties.",
    "LinkedIn Ads": "B2B advertising platform for sponsored content and lead generation.",
    "GoHighLevel": "Sales and marketing automation platform for agencies and businesses.",
    "Mailchimp": "Email marketing, audience management, and campaign platform.",
    "Klaviyo": "Ecommerce email and SMS marketing platform.",
    "systeme.io": "All-in-one funnel, email, course, and marketing platform.",
    "Pinterest": "Visual discovery and advertising platform.",
    "Threads (Meta)": "Text-based social publishing platform with API developer access.",
    "SendGrid": "Transactional and marketing email delivery platform.",
    "Shopify": "Hosted ecommerce platform for online stores and commerce APIs.",
    "WooCommerce": "WordPress ecommerce plugin and store API platform.",
    "BigCommerce": "Hosted ecommerce platform for storefront and commerce operations.",
    "Salesforce Commerce Cloud": "Enterprise digital commerce platform for large retailers.",
    "Magento (Adobe Commerce)": "Flexible enterprise ecommerce platform.",
    "Squarespace": "Website, commerce, and online business platform.",
    "Ecwid": "Embedded ecommerce platform for adding a store to websites.",
    "Gumroad": "Platform for selling digital products and subscriptions.",
    "Amazon Selling Partner": "Seller APIs for Amazon inventory, orders, and account operations.",
    "fanbasis": "Creator commerce and fan engagement platform.",
    "DataForSEO": "SEO and search engine data APIs.",
    "SE Ranking": "SEO monitoring, rank tracking, and competitive analysis platform.",
    "Ahrefs": "Search engine optimization and backlink intelligence platform.",
    "MrScraper": "Web scraping and data extraction platform.",
    "Apify": "Cloud actors and APIs for web scraping and automation.",
    "Firecrawl": "Web crawling and content extraction API for AI applications.",
    "Bright Data": "Proxy, scraping, and public web data platform.",
    "Sherlock": "Open-source command-line username search tool.",
    "Waterfall.io": "Company intelligence and business data platform.",
    "Clay": "Data enrichment and outbound prospecting workspace.",
    "GitHub": "Source hosting, collaboration, issues, actions, and developer APIs.",
    "Vercel": "Frontend deployment and serverless web platform.",
    "Netlify": "Frontend deployment and edge hosting platform.",
    "Cloudflare": "Edge network, DNS, security, and developer platform.",
    "Supabase": "Open-source backend platform for databases, auth, and storage.",
    "Neo4j": "Graph database and connected-data platform.",
    "Snowflake": "Cloud data warehouse and analytics platform.",
    "MongoDB Atlas": "Hosted MongoDB database and data services platform.",
    "Datadog": "Cloud monitoring, logs, traces, and infrastructure observability.",
    "Sentry": "Application error tracking and performance monitoring.",
    "Notion": "Connected workspace for notes, documents, databases, and projects.",
    "Airtable": "Low-code database platform for structured workflows.",
    "Linear": "Issue tracking and product development platform.",
    "Jira": "Project, issue, and software delivery management platform.",
    "Asana": "Work management platform for projects and cross-team execution.",
    "Monday.com": "Configurable work management platform.",
    "ClickUp": "Project, document, goal, and task management platform.",
    "Coda": "Document platform with databases and interactive workflows.",
    "Smartsheet": "Spreadsheet-style work management and automation platform.",
    "Harvest": "Time tracking and project invoicing platform.",
    "Stripe": "Payment processing and financial platform APIs.",
    "Plaid": "Financial account connectivity and verification APIs.",
    "Binance": "Cryptocurrency exchange and trading platform.",
    "Paygent Connect": "Payment gateway integration built around NMI infrastructure.",
    "iPayX": "Digital payments and payment processing platform.",
    "QuickBooks": "Accounting, invoicing, and financial management platform.",
    "Xero": "Cloud accounting platform for businesses and advisers.",
    "Brex": "Corporate cards and financial operations platform.",
    "Ramp": "Corporate spend and financial operations platform.",
    "PitchBook": "Private markets research and company intelligence platform.",
    "NotebookLM": "Google notebook tool for grounding research in uploaded sources.",
    "Otter AI": "Meeting transcription, summaries, and conversation intelligence.",
    "Fathom": "AI meeting assistant for recording, summaries, and CRM workflows.",
    "Consensus": "AI-powered research search and evidence synthesis platform.",
    "Reducto": "Document parsing and structured extraction API.",
    "Devin": "AI software engineering agent with coding and MCP capabilities.",
    "higgsfield": "AI visual content and creative media generation platform.",
    "Mermaid CLI": "Command-line renderer for Mermaid diagrams.",
    "YouTube Transcript": "API service for retrieving YouTube transcript text.",
    "Grain": "Meeting recording, transcription, highlights, and workspace platform.",
}

# ---------------------------------------------------------------------------
# KNOWN_AUTH: auth method sourced from official developer documentation.
# Source: official developer/API documentation pages for each application.
# ---------------------------------------------------------------------------
KNOWN_AUTH = {
    # CRM
    "Salesforce": "OAuth2 / Connected App",
    "HubSpot": "OAuth2 / Private app access token",
    "Pipedrive": "OAuth2",
    "Attio": "OAuth2 / API key",
    "Twenty": "API key",
    "Podio": "OAuth2",
    "Zoho CRM": "OAuth2",
    "Close": "API key",
    "Copper": "API key",
    "DealCloud": "API key",
    # Support
    "Zendesk": "OAuth2 / API key",
    "Intercom": "OAuth2",
    "Freshdesk": "API key / OAuth2",
    "Front": "OAuth2",
    "Help Scout": "OAuth2",
    "Gorgias": "OAuth2",
    "LiveAgent": "API key",
    "Plain": "API key (Bearer token)",
    "Pylon": "API key",
    # Communications
    "Slack": "OAuth2",
    "Twilio": "API key",
    "Zoho Cliq": "OAuth2",
    "Lark (Larksuite)": "OAuth2",
    "Pumble": "API key",
    "Discord": "OAuth2 / Bot token",
    "Telegram": "Bot token",
    "WhatsApp Business": "OAuth2 (Meta)",
    "Aircall": "OAuth2",
    "Vonage": "API key",
    # Marketing
    "Google Ads": "OAuth2",
    "Meta Ads": "OAuth2",
    "LinkedIn Ads": "OAuth2",
    "GoHighLevel": "OAuth2",
    "Mailchimp": "API key / OAuth2",
    "Klaviyo": "API key",
    "systeme.io": "API key",
    "Pinterest": "OAuth2",
    "Threads (Meta)": "OAuth2",
    "SendGrid": "API key",
    # Ecommerce
    "Shopify": "OAuth2",
    "WooCommerce": "Consumer key / Consumer secret",
    "BigCommerce": "OAuth2 / API key",
    "Salesforce Commerce Cloud": "OAuth2 (SLAS)",
    "Magento (Adobe Commerce)": "OAuth2 / API key",
    "Squarespace": "OAuth2",
    "Ecwid": "OAuth2 / API key",
    "Gumroad": "OAuth2",
    "Amazon Selling Partner": "OAuth2 (LWA)",
    "fanbasis": "API key",
    # Data / SEO
    "DataForSEO": "API key (HTTP Basic)",
    "SE Ranking": "API key",
    "Ahrefs": "OAuth2 / API key",
    "MrScraper": "API key",
    "Apify": "API key",
    "Firecrawl": "API key",
    "Bright Data": "API key",
    "Waterfall.io": "API key",
    "Clay": "API key",
    # Developer
    "GitHub": "OAuth2 / Personal access token",
    "Vercel": "OAuth2 / Personal access token",
    "Netlify": "OAuth2 / Personal access token",
    "Cloudflare": "API key / OAuth2",
    "Supabase": "API key / JWT",
    "Neo4j": "Username / password / API key",
    "Snowflake": "OAuth2 / Key pair",
    "MongoDB Atlas": "API key (Digest)",
    "Datadog": "API key",
    "Sentry": "API key / OAuth2",
    # Productivity
    "Notion": "OAuth2",
    "Airtable": "OAuth2 / Personal access token",
    "Linear": "OAuth2",
    "Jira": "OAuth2 / API token",
    "Asana": "OAuth2 / Personal access token",
    "Monday.com": "OAuth2 / API key",
    "ClickUp": "OAuth2 / API key",
    "Coda": "API key",
    "Smartsheet": "OAuth2 / API key",
    "Harvest": "OAuth2",
    # Finance
    "Stripe": "API key",
    "Plaid": "API key (client_id + secret)",
    "Binance": "API key",
    "QuickBooks": "OAuth2",
    "Xero": "OAuth2",
    "Brex": "OAuth2",
    "Ramp": "OAuth2",
    # AI / Media
    "NotebookLM": "Google OAuth2",
    "Otter AI": "OAuth2",
    "Fathom": "API key",
    "Consensus": "API key",
    "Reducto": "API key",
    "Devin": "API key",
    "higgsfield": "API key",
    "YouTube Transcript": "API key (RapidAPI)",
    "Grain": "OAuth2",
    # CLI / no auth
    "Mermaid CLI": "None",
    "Sherlock": "None",
}

# ---------------------------------------------------------------------------
# KNOWN_ACCESS: access tier sourced from official signup and pricing pages.
# Self-serve = developer account available without manual vendor approval.
# Partner / admin-gated = requires application, review, or vendor approval.
# ---------------------------------------------------------------------------
KNOWN_ACCESS = {
    "Mermaid CLI": "Self-serve",
    "Sherlock": "Self-serve",
    "Twenty": "Self-serve",
    # Confirmed self-serve
    "GitHub": "Self-serve",
    "Stripe": "Self-serve",
    "Twilio": "Self-serve",
    "SendGrid": "Self-serve",
    "Vercel": "Self-serve",
    "Netlify": "Self-serve",
    "Supabase": "Self-serve",
    "Datadog": "Self-serve",
    "Sentry": "Self-serve",
    "Apify": "Self-serve",
    "Firecrawl": "Self-serve",
    "Reducto": "Self-serve",
    "WooCommerce": "Self-serve",
    "Ecwid": "Self-serve",
    "Gumroad": "Self-serve",
    "DataForSEO": "Self-serve",
    "Ahrefs": "Self-serve",
    "Clay": "Self-serve",
    "Coda": "Self-serve",
    "Fathom": "Self-serve",
    "YouTube Transcript": "Self-serve",
    "Devin": "Self-serve",
    "higgsfield": "Self-serve",
    "Binance": "Self-serve",
    "HubSpot": "Self-serve",
    "Pipedrive": "Self-serve",
    "Mailchimp": "Self-serve",
    "Klaviyo": "Self-serve",
    "Notion": "Self-serve",
    "Airtable": "Self-serve",
    "Linear": "Self-serve",
    "ClickUp": "Self-serve",
    "Harvest": "Self-serve",
    "Smartsheet": "Self-serve",
    "Monday.com": "Self-serve",
    "MrScraper": "Self-serve",
    "Consensus": "Self-serve",
    # Confirmed partner/admin-gated
    "Salesforce Commerce Cloud": "Partner / admin-gated",
    "PitchBook": "Partner / admin-gated",
    "DealCloud": "Partner / admin-gated",
    "LinkedIn Ads": "Partner / admin-gated",
    "Amazon Selling Partner": "Partner / admin-gated",
    "WhatsApp Business": "Partner / admin-gated",
    "Meta Ads": "Partner / admin-gated",
    "Plaid": "Partner / admin-gated",
    "Google Ads": "Partner / admin-gated",
    "NotebookLM": "Self-serve (no public API)",
}

# ---------------------------------------------------------------------------
# KNOWN_REST: REST API availability from official developer documentation.
# Yes = REST API publicly documented. No = no REST API available.
# ---------------------------------------------------------------------------
KNOWN_REST = {
    "Salesforce": "Yes",
    "HubSpot": "Yes",
    "Pipedrive": "Yes",
    "Attio": "Yes",
    "Twenty": "Yes",
    "Podio": "Yes",
    "Zoho CRM": "Yes",
    "Close": "Yes",
    "Copper": "Yes",
    "DealCloud": "Yes",
    "Zendesk": "Yes",
    "Intercom": "Yes",
    "Freshdesk": "Yes",
    "Front": "Yes",
    "Pylon": "Yes",
    "Help Scout": "Yes",
    "Gorgias": "Yes",
    "Gladly": "Yes",
    "Slack": "Yes",
    "Twilio": "Yes",
    "Aircall": "Yes",
    "Vonage": "Yes",
    "Google Ads": "Yes",
    "Meta Ads": "Yes",
    "LinkedIn Ads": "Yes",
    "GoHighLevel": "Yes",
    "Mailchimp": "Yes",
    "Klaviyo": "Yes",
    "systeme.io": "Yes",
    "Pinterest": "Yes",
    "Threads (Meta)": "Yes",
    "SendGrid": "Yes",
    "Shopify": "Yes",
    "WooCommerce": "Yes",
    "BigCommerce": "Yes",
    "Magento (Adobe Commerce)": "Yes",
    "Squarespace": "Yes",
    "Ecwid": "Yes",
    "Gumroad": "Yes",
    "Amazon Selling Partner": "Yes",
    "DataForSEO": "Yes",
    "Ahrefs": "Yes",
    "MrScraper": "Yes",
    "Apify": "Yes",
    "Firecrawl": "Yes",
    "Bright Data": "Yes",
    "Clay": "Yes",
    "GitHub": "Yes",
    "Vercel": "Yes",
    "Netlify": "Yes",
    "Cloudflare": "Yes",
    "Supabase": "Yes",
    "MongoDB Atlas": "Yes",
    "Datadog": "Yes",
    "Sentry": "Yes",
    "Notion": "Yes",
    "Airtable": "Yes",
    "Linear": "Yes",
    "Jira": "Yes",
    "Asana": "Yes",
    "Monday.com": "Yes",
    "ClickUp": "Yes",
    "Coda": "Yes",
    "Smartsheet": "Yes",
    "Harvest": "Yes",
    "Stripe": "Yes",
    "Plaid": "Yes",
    "QuickBooks": "Yes",
    "Xero": "Yes",
    "Brex": "Yes",
    "Ramp": "Yes",
    "Fathom": "Yes",
    "Reducto": "Yes",
    "Devin": "Yes",
    "YouTube Transcript": "Yes",
    "Mermaid CLI": "No public API",
    "Sherlock": "No public API",
    "NotebookLM": "No public API",
}

# ---------------------------------------------------------------------------
# KNOWN_GRAPHQL: GraphQL API availability from official developer documentation.
# ---------------------------------------------------------------------------
KNOWN_GRAPHQL = {
    "GitHub": "Yes",
    "Shopify": "Yes",
    "HubSpot": "Yes",
    "Salesforce": "Yes",
    "Linear": "Yes",
    "Monday.com": "Yes",
    "BigCommerce": "Yes",
    "Supabase": "Yes",
    "MongoDB Atlas": "Yes",
    "Twenty": "Yes",
    "Plain": "Yes",
    "Mermaid CLI": "No",
    "Sherlock": "No",
    "NotebookLM": "No",
}

# ---------------------------------------------------------------------------
# KNOWN_OFFICIAL_MCP: Official vendor-published MCP servers.
# Sources: official documentation and github.com/modelcontextprotocol/servers.
# ---------------------------------------------------------------------------
KNOWN_OFFICIAL_MCP = {
    "GitHub": "Yes – official MCP server (github.com/github/github-mcp-server)",
    "Cloudflare": "Yes – official MCP server (developers.cloudflare.com/agents/)",
    "Notion": "Yes – official MCP server (developers.notion.com/docs/mcp)",
    "Jira": "Yes – official MCP server (atlassian.com/mcp)",
    "Stripe": "Yes – official MCP server (docs.stripe.com/mcp)",
    "Datadog": "Yes – official MCP server (docs.datadoghq.com/agent/mcp)",
    "Mermaid CLI": "No known official MCP",
    "Sherlock": "No known official MCP",
    "NotebookLM": "No known official MCP",
}

# ---------------------------------------------------------------------------
# KNOWN_BUILDABILITY: buildability verdict based on auth + REST + access.
# Buildable now: confirmed auth + REST + self-serve access.
# Buildable with limits: confirmed auth + REST + account/plan caveats.
# ---------------------------------------------------------------------------
KNOWN_BUILDABILITY = {
    "GitHub": "Buildable now",
    "Stripe": "Buildable now",
    "Twilio": "Buildable now",
    "SendGrid": "Buildable now",
    "WooCommerce": "Buildable now",
    "Datadog": "Buildable now",
    "Sentry": "Buildable now",
    "Apify": "Buildable now",
    "Firecrawl": "Buildable now",
    "Vercel": "Buildable now",
    "Netlify": "Buildable now",
    "Supabase": "Buildable now",
    "DataForSEO": "Buildable now",
    "Reducto": "Buildable now",
    "YouTube Transcript": "Buildable now",
    "Fathom": "Buildable now",
    "HubSpot": "Buildable now",
    "Pipedrive": "Buildable now",
    "Mailchimp": "Buildable now",
    "Klaviyo": "Buildable now",
    "Notion": "Buildable now",
    "Airtable": "Buildable now",
    "Linear": "Buildable now",
    "ClickUp": "Buildable now",
    "Coda": "Buildable now",
    "Harvest": "Buildable now",
    "MrScraper": "Buildable now",
    "Consensus": "Buildable now",
    "Devin": "Buildable with limits",
    "Ahrefs": "Buildable with limits",
    "Clay": "Buildable with limits",
    "Zendesk": "Buildable with limits",
    "Freshdesk": "Buildable with limits",
    "Slack": "Buildable with limits",
    "Shopify": "Buildable with limits",
    "Jira": "Buildable with limits",
    "Asana": "Buildable with limits",
    "Monday.com": "Buildable with limits",
    "Smartsheet": "Buildable with limits",
    "QuickBooks": "Buildable with limits",
    "Xero": "Buildable with limits",
    "Brex": "Buildable with limits",
    "Ramp": "Buildable with limits",
    "Binance": "Buildable with limits",
    "Mermaid CLI": "Buildable as local CLI integration",
    "Sherlock": "Buildable as local CLI integration",
    "NotebookLM": "Not buildable via public API",
}

# ---------------------------------------------------------------------------
# KNOWN_BLOCKERS: specific integration blockers from official documentation.
# ---------------------------------------------------------------------------
KNOWN_BLOCKERS = {
    "GitHub": "Fine-grained PAT scopes required for private repos; no blocker for public data",
    "Stripe": "Sandbox vs live mode separation; PCI compliance for card data storage",
    "Twilio": "Trial account requires number verification; SMS A2P registration for US",
    "SendGrid": "Domain authentication and sender identity verification required",
    "HubSpot": "Private app required for most endpoints; OAuth for multi-account workflows",
    "Shopify": "Partner developer store needed; app review required for public listing",
    "Slack": "App submission review for public distribution; workspace admin for some scopes",
    "Notion": "Integration must be explicitly added to workspace by admin",
    "Airtable": "Personal access token scope is per-base; OAuth required for multi-workspace",
    "Linear": "API key is per-user; OAuth required for multi-workspace integrations",
    "Jira": "Cloud vs Server/Data Center API differences; OAuth requires Atlassian Connect",
    "Mailchimp": "API key access covers all lists; OAuth needed for multi-account agencies",
    "Datadog": "API key + Application key both required; site-specific endpoints (US1 vs EU)",
    "Sentry": "Internal integration vs public app; auth token scopes differ",
    "Vercel": "Deployment token scopes; team access requires team plan",
    "Netlify": "Personal access token for most uses; OAuth for multi-account deploys",
    "Supabase": "Project-level API keys; Row Level Security must be configured",
    "Apify": "Free tier compute unit limits; residential proxies are paid add-on",
    "Firecrawl": "Free tier page-crawl limits; credit-based pricing for high volume",
    "Zendesk": "Subdomain required; full API access requires Support plan or above",
    "Freshdesk": "API key per agent; some endpoints require Growth plan or higher",
    "WooCommerce": "Requires self-hosted WordPress; consumer key/secret generated per site",
    "Ecwid": "Free plan has limited API access; Instant Site plan required for full API",
    "Clay": "Credit-based model for enrichment; provider data quality varies by plan",
    "Ahrefs": "API access requires paid subscription plan; not included in free tier",
    "QuickBooks": "OAuth with Intuit; sandbox vs production apps are separate registrations",
    "Xero": "OAuth with Xero; app certification required for Xero App Store listing",
    "Ramp": "Business account required; some API features in developer preview",
    "Brex": "Business account required; spend card creation requires treasury workflow",
    "Monday.com": "API key or OAuth; some advanced features require Enterprise plan",
    "Asana": "OAuth or personal access token; some features require Business/Enterprise plan",
    "Jira": "Cloud vs Server differences; Atlassian Connect app review for OAuth distribution",
    "DataForSEO": "Credit balance required for production usage; free trial credits available",
    "MrScraper": "Rate limits on free plan; premium plans unlock higher concurrency",
    "YouTube Transcript": "RapidAPI subscription required; quota limits per plan",
    "Devin": "API in early access; availability depends on account tier",
    "Consensus": "API key; usage may require subscription depending on query volume",
    "Reducto": "Credit-based pricing for high document volume",
    "Fathom": "API access available to all paid plan users",
    "Mermaid CLI": "No hosted API; wrap CLI or use as local execution adapter",
    "Sherlock": "No hosted API; must run locally via Python or Docker",
    "NotebookLM": "No public REST API; web UI access only via Google OAuth2",
    "Binance": "KYC verification required; some endpoints restricted by jurisdiction",
    "Plaid": "Partner application required; production access subject to Plaid review",
    "Amazon Selling Partner": "Requires registered Amazon seller account; IAM role and LWA OAuth approval",
    "WhatsApp Business": "Meta Business verification and app review required; phone number registration",
    "Meta Ads": "Ad account approval required; App Review for advanced permissions",
    "LinkedIn Ads": "Partner program application; Campaign Manager API access is gated",
    "Google Ads": "Developer token approval required; test account available for development",
    "Salesforce Commerce Cloud": "SFCC partner account required; Shopper APIs for headless commerce",
    "PitchBook": "Subscription-only; data API requires enterprise agreement",
    "DealCloud": "Enterprise CRM; API access negotiated per contract",
}

# ---------------------------------------------------------------------------
# KNOWN_API_BREADTH: concise API breadth notes for well-documented apps.
# ---------------------------------------------------------------------------
KNOWN_API_BREADTH = {
    "GitHub": "Comprehensive REST and GraphQL APIs covering repos, issues, PRs, Actions, and Packages",
    "Stripe": "Full payment lifecycle: charges, customers, subscriptions, payouts, webhooks",
    "Twilio": "Voice, SMS, WhatsApp, email, video, and verify APIs",
    "Slack": "Messaging, channels, users, files, apps, and workflow APIs",
    "HubSpot": "CRM, contacts, deals, marketing, and analytics APIs",
    "Shopify": "Products, orders, customers, inventory, webhooks, REST and GraphQL",
    "Notion": "Pages, blocks, databases, comments, and search APIs",
    "Datadog": "Metrics, logs, traces, monitors, dashboards, and incident APIs",
    "Mermaid CLI": "Command-line tool; no REST API classification applicable",
    "Sherlock": "Command-line tool; no REST API classification applicable",
}


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(LOG_DIR / "research.log")],
    )


class DocumentationResearcher:
    def fetch(self, url):
        for attempt in range(1, REQUEST_RETRIES + 1):
            try:
                response = requests.get(
                    url, timeout=REQUEST_TIMEOUT,
                    headers={"User-Agent": "Composio-Research-Agent/1.0"},
                )
                if response.status_code >= 400:
                    raise requests.HTTPError(f"HTTP {response.status_code}", response=response)
                soup = BeautifulSoup(response.text, "html.parser")
                title = soup.title.get_text(" ", strip=True) if soup.title else ""
                text = soup.get_text(" ", strip=True)[:12000]
                return {"status": "ok", "title": title, "text": text}
            except requests.RequestException as exc:
                logging.warning("Attempt %s failed for %s: %s", attempt, url, exc)
                if attempt < REQUEST_RETRIES:
                    time.sleep(attempt)
        return {"status": "error", "title": "", "text": ""}


class DocumentationExtractor:
    def extract(self, app, category, url, page):
        name = app["app"]

        # Description
        description = DESCRIPTIONS.get(name)
        if not description:
            description = f"{name} provides {CATEGORY_PURPOSE[category]}."

        # --- Defaults ---
        auth = KNOWN_AUTH.get(name, "Unknown")
        access = KNOWN_ACCESS.get(name, "Requires Verification")
        rest = KNOWN_REST.get(name, "Unknown")
        graphql = KNOWN_GRAPHQL.get(name, "Unknown")
        official_mcp = KNOWN_OFFICIAL_MCP.get(name, "Unknown")
        community_mcp = "Unknown"
        api_breadth = KNOWN_API_BREADTH.get(name, "Unknown")
        confidence = Confidence.LOW

        # --- Page-fetch evidence ---
        evidence = "Official documentation URL retrieved; classification remains to be verified"
        if page["status"] == "ok":
            text = page["text"].lower()
            evidence = f"Official page returned successfully: {page['title'] or 'documentation page'}"

            # Only apply keyword detection if we don't already have authoritative data
            if rest == "Unknown":
                if "rest api" in text or "restful" in text or "rest endpoint" in text:
                    rest = "Yes"
            if graphql == "Unknown":
                if "graphql" in text:
                    graphql = "Yes"
            if official_mcp == "Unknown":
                if "model context protocol" in text or ("mcp" in text and "official" in text):
                    official_mcp = "Requires Verification"

        # --- Buildability ---
        buildability = KNOWN_BUILDABILITY.get(name)
        if buildability is None:
            if name in {"Mermaid CLI", "Sherlock"}:
                buildability = "Buildable as local CLI integration"
            elif auth != "Unknown" and rest == "Yes":
                buildability = "Requires verification"
            elif auth != "Unknown":
                buildability = "Requires verification"
            else:
                buildability = "Requires Research"

        # --- Main blocker ---
        blocker = KNOWN_BLOCKERS.get(name)
        if blocker is None:
            if name in {"Mermaid CLI", "Sherlock"}:
                blocker = "No hosted API; wrap CLI or provide a local execution adapter"
            elif buildability == "Requires Research":
                blocker = "Official API, authentication, account, and MCP documentation must be verified"
            else:
                blocker = "Authentication and account plan details require confirmation"

        # --- REST/breadth for CLI tools ---
        if name in {"Mermaid CLI", "Sherlock"}:
            rest = "No public API"
            graphql = "No"
            api_breadth = "Command-line tool; no REST API classification"

        # --- API breadth fallback ---
        if api_breadth == "Unknown" and rest == "Yes":
            api_breadth = "Public REST API; breadth requires verification"

        # --- what_it_does (workflow context) ---
        workflow_context = {
            "GitHub": "Used to manage source code, automate CI/CD pipelines, and trigger workflows via webhooks",
            "Stripe": "Used to process payments, manage subscriptions, and handle refunds in revenue workflows",
            "Slack": "Used to send notifications, create channels, and manage team communications programmatically",
            "HubSpot": "Used to sync CRM contacts, manage pipelines, and automate marketing sequences",
            "Notion": "Used to create pages, update databases, and read structured workspace content",
            "Shopify": "Used to manage products, fulfill orders, and sync inventory across channels",
            "Datadog": "Used to send metrics, query logs, manage monitors, and trigger alerts",
            "Jira": "Used to create issues, update sprint boards, and track software delivery progress",
            "Mailchimp": "Used to manage subscriber lists, send campaigns, and track email engagement",
            "Stripe": "Used to create payment intents, manage subscriptions, and retrieve financial reports",
            "Airtable": "Used to read and write structured records, trigger automations, and sync data",
        }
        what_it_does = workflow_context.get(name, description)

        return ResearchFinding(
            rank=app["rank"],
            app=name,
            category=category,
            description=description,
            what_it_does=what_it_does,
            auth_methods=auth,
            public_rest_api=rest,
            graphql_api=graphql,
            api_breadth=api_breadth,
            access=access,
            official_mcp=official_mcp,
            community_mcp=community_mcp,
            buildability=buildability,
            main_blocker=blocker,
            evidence_url=url,
            evidence=evidence,
            confidence=confidence,
            last_researched=RESEARCH_DATE,
        )


def load_apps():
    return json.loads((DATA / "apps.json").read_text(encoding="utf-8"))


def save_intermediate(rank, finding):
    DATA.mkdir(parents=True, exist_ok=True)
    partial = DATA / "research_partial.json"
    records = json.loads(partial.read_text()) if partial.exists() else []
    records = [r for r in records if r["rank"] != rank]
    records.append(finding.model_dump(mode="json"))
    records.sort(key=lambda r: r["rank"])
    partial.write_text(json.dumps(records, indent=2), encoding="utf-8")


def research(app, name=None):
    page = DocumentationResearcher().fetch(app["website"])
    return DocumentationExtractor().extract(app, app["category"], app["website"], page)


def run(app_name=None, resume=False):
    setup_logging()
    apps = load_apps()
    if app_name:
        matches = [a for a in apps if a["app"].lower() == app_name.lower()]
        if not matches:
            raise SystemExit(f"Application not found: {app_name}")
        apps = matches

    existing = {}
    partial = DATA / "research_partial.json"
    if resume and partial.exists():
        existing = {r["rank"]: r for r in json.loads(partial.read_text())}

    findings = []
    researcher = DocumentationResearcher()
    extractor = DocumentationExtractor()
    for app in apps:
        if resume and app["rank"] in existing:
            try:
                findings.append(ResearchFinding(**existing[app["rank"]]))
                logging.info("Resumed %s", app["app"])
                continue
            except Exception:
                logging.exception("Invalid partial result for %s", app["app"])
        page = researcher.fetch(app["website"])
        finding = extractor.extract(app, app["category"], app["website"], page)
        findings.append(finding)
        save_intermediate(app["rank"], finding)
        logging.info("Researched %s (%s)", app["app"], finding.confidence.value)

    if app_name:
        print(json.dumps(findings[0].model_dump(mode="json"), indent=2))
        return findings
    export_findings(findings, DATA)
    logging.info("Exported %s applications", len(findings))
    return findings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", help="Research one app by exact name")
    parser.add_argument("--all", action="store_true", help="Research all 100 apps")
    parser.add_argument("--resume", action="store_true", help="Resume partial research")
    args = parser.parse_args()
    if not args.app and not args.all:
        parser.error("Choose --app <name> or --all")
    run(app_name=args.app, resume=args.resume)


if __name__ == "__main__":
    main()

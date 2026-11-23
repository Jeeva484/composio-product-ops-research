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
"CRM and Sales":"customer relationship, pipeline, and sales workflow",
"Support and Helpdesk":"customer support, ticketing, and service operations",
"Communications and Messaging":"team or customer communication",
"Marketing, Ads, Email and Social":"campaign, audience, email, and publishing workflows",
"Ecommerce":"storefront, commerce, and marketplace operations",
"Data, SEO and Scraping":"search, web data, enrichment, or scraping workflows",
"Developer, Infra and Data platforms":"developer workflows, infrastructure, or data services",
"Productivity and Project Management":"planning, documents, and team execution",
"Finance and Fintech":"payments, accounting, treasury, or financial operations",
"AI, Research and Media-native":"AI research, generation, transcription, or media workflows",
}

DESCRIPTIONS = {
"Salesforce":"Cloud CRM for sales, service, marketing, and customer data.","HubSpot":"CRM and marketing platform for contacts, campaigns, and revenue workflows.",
"Pipedrive":"Sales CRM for pipeline and deal management.","Attio":"Flexible CRM for structured customer and relationship data.",
"Twenty":"Open-source CRM for managing people, companies, and opportunities.","Podio":"Customizable work and team management platform.",
"Zoho CRM":"CRM platform for lead, account, pipeline, and sales automation.","Close":"Sales CRM designed for outbound calling and pipeline workflows.",
"Copper":"CRM for managing sales relationships and Google Workspace workflows.","DealCloud":"Enterprise CRM and deal-management platform for alternative investments.",
"Zendesk":"Customer support platform for ticketing and omnichannel service.","Intercom":"Customer messaging platform for support, sales, and product engagement.",
"Freshdesk":"Helpdesk platform for ticket management and customer support.","Front":"Shared inbox and collaborative customer communication platform.",
"Pylon":"Support platform for B2B customer service and account workflows.","LiveAgent":"Helpdesk and live-chat platform for customer support.",
"Plain":"Developer-oriented support platform for customer interactions.","Help Scout":"Shared-inbox and knowledge-base support platform.",
"Gorgias":"Ecommerce-focused customer service and helpdesk platform.","Gladly":"Customer service platform built around long-lived conversations.",
"Slack":"Team messaging platform with channels, apps, workflows, and search.","Twilio":"Cloud communications platform for voice, SMS, email, and messaging.",
"Zoho Cliq":"Team chat and collaboration platform.","Lark (Larksuite)":"Collaboration suite for chat, meetings, documents, and workflows.",
"Pumble":"Team chat platform for messaging and collaboration.","Discord":"Community and team communication platform with servers and bots.",
"Telegram":"Messaging platform with bots and channel-based communication.","WhatsApp Business":"Business messaging platform for customer conversations.",
"Aircall":"Cloud business phone system with call routing and integrations.","Vonage":"Communications APIs for voice, messaging, video, and verification.",
"Google Ads":"Advertising platform for search, display, video, and campaign reporting.","Meta Ads":"Advertising platform for campaigns across Meta properties.",
"LinkedIn Ads":"B2B advertising platform for sponsored content and lead generation.","GoHighLevel":"Sales and marketing automation platform for agencies and businesses.",
"Mailchimp":"Email marketing, audience management, and campaign platform.","Klaviyo":"Ecommerce email and SMS marketing platform.",
"systeme.io":"All-in-one funnel, email, course, and marketing platform.","Pinterest":"Visual discovery and advertising platform.",
"Threads (Meta)":"Text-based social publishing platform with API developer access.","SendGrid":"Transactional and marketing email delivery platform.",
"Shopify":"Hosted ecommerce platform for online stores and commerce APIs.","WooCommerce":"WordPress ecommerce plugin and store API platform.",
"BigCommerce":"Hosted ecommerce platform for storefront and commerce operations.","Salesforce Commerce Cloud":"Enterprise digital commerce platform for large retailers.",
"Magento (Adobe Commerce)":"Flexible enterprise ecommerce platform.","Squarespace":"Website, commerce, and online business platform.",
"Ecwid":"Embedded ecommerce platform for adding a store to websites.","Gumroad":"Platform for selling digital products and subscriptions.",
"Amazon Selling Partner":"Seller APIs for Amazon inventory, orders, and account operations.","fanbasis":"Creator commerce and fan engagement platform.",
"DataForSEO":"SEO and search engine data APIs.","SE Ranking":"SEO monitoring, rank tracking, and competitive analysis platform.",
"Ahrefs":"Search engine optimization and backlink intelligence platform.","MrScraper":"Web scraping and data extraction platform.",
"Apify":"Cloud actors and APIs for web scraping and automation.","Firecrawl":"Web crawling and content extraction API for AI applications.",
"Bright Data":"Proxy, scraping, and public web data platform.","Sherlock":"Open-source command-line username search tool.",
"Waterfall.io":"Company intelligence and business data platform.","Clay":"Data enrichment and outbound prospecting workspace.",
"GitHub":"Source hosting, collaboration, issues, actions, and developer APIs.","Vercel":"Frontend deployment and serverless web platform.",
"Netlify":"Frontend deployment and edge hosting platform.","Cloudflare":"Edge network, DNS, security, and developer platform.",
"Supabase":"Open-source backend platform for databases, auth, and storage.","Neo4j":"Graph database and connected-data platform.",
"Snowflake":"Cloud data warehouse and analytics platform.","MongoDB Atlas":"Hosted MongoDB database and data services platform.",
"Datadog":"Cloud monitoring, logs, traces, and infrastructure observability.","Sentry":"Application error tracking and performance monitoring.",
"Notion":"Connected workspace for notes, documents, databases, and projects.","Airtable":"Low-code database platform for structured workflows.",
"Linear":"Issue tracking and product development platform.","Jira":"Project, issue, and software delivery management platform.",
"Asana":"Work management platform for projects and cross-team execution.","Monday.com":"Configurable work management platform.",
"ClickUp":"Project, document, goal, and task management platform.","Coda":"Document platform with databases and interactive workflows.",
"Smartsheet":"Spreadsheet-style work management and automation platform.","Harvest":"Time tracking and project invoicing platform.",
"Stripe":"Payment processing and financial platform APIs.","Plaid":"Financial account connectivity and verification APIs.",
"Binance":"Cryptocurrency exchange and trading platform.","Paygent Connect":"Payment gateway integration built around NMI infrastructure.",
"iPayX":"Digital payments and payment processing platform.","QuickBooks":"Accounting, invoicing, and financial management platform.",
"Xero":"Cloud accounting platform for businesses and advisers.","Brex":"Corporate cards and financial operations platform.",
"Ramp":"Corporate spend and financial operations platform.","PitchBook":"Private markets research and company intelligence platform.",
"NotebookLM":"Google notebook tool for grounding research in uploaded sources.","Otter AI":"Meeting transcription, summaries, and conversation intelligence.",
"Fathom":"AI meeting assistant for recording, summaries, and CRM workflows.","Consensus":"AI-powered research search and evidence synthesis platform.",
"Reducto":"Document parsing and structured extraction API.","Devin":"AI software engineering agent with coding and MCP capabilities.",
"higgsfield":"AI visual content and creative media generation platform.","Mermaid CLI":"Command-line renderer for Mermaid diagrams.",
"YouTube Transcript":"API service for retrieving YouTube transcript text.","Grain":"Meeting recording, transcription, highlights, and workspace platform.",
}

KNOWN_AUTH = {
"Mermaid CLI":"None","Sherlock":"None","Stripe":"API key","Twilio":"API key",
"SendGrid":"API key","Binance":"API key","Slack":"OAuth2","GitHub":"OAuth2 / Personal access token",
"Notion":"OAuth2","Airtable":"OAuth2 / Personal access token","Linear":"OAuth2",
"Shopify":"OAuth2","WooCommerce":"Consumer key / Consumer secret","Telegram":"Bot token",
"Discord":"OAuth2 / Bot token","HubSpot":"OAuth2 / Private app access token",
"Pipedrive":"OAuth2","Xero":"OAuth2","QuickBooks":"OAuth2","Atlassian Jira":"OAuth2",
"Jira":"OAuth2","Harvest":"OAuth2","Vercel":"OAuth2 / Personal access token",
}

KNOWN_ACCESS = {"Mermaid CLI":"Self-serve","Sherlock":"Self-serve","Twenty":"Self-serve"}

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
                response = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent":"Composio-Research-Agent/1.0"})
                if response.status_code >= 400:
                    raise requests.HTTPError(f"HTTP {response.status_code}", response=response)
                soup = BeautifulSoup(response.text, "html.parser")
                title = soup.title.get_text(" ", strip=True) if soup.title else ""
                text = soup.get_text(" ", strip=True)[:12000]
                return {"status":"ok","title":title,"text":text}
            except requests.RequestException as exc:
                logging.warning("Attempt %s failed for %s: %s", attempt, url, exc)
                if attempt < REQUEST_RETRIES:
                    time.sleep(attempt)
        return {"status":"error","title":"","text":""}

class DocumentationExtractor:
    def extract(self, app, category, url, page):
        name = app["app"]
        auth = KNOWN_AUTH.get(name, "Unknown")
        access = KNOWN_ACCESS.get(name, "Requires Verification")
        rest = "Unknown"
        graphql = "Unknown"
        breadth = "Unknown"
        official_mcp = "Unknown"
        community_mcp = "Unknown"
        description = DESCRIPTIONS.get(name)
        if not description:
            description = f"{name} provides {CATEGORY_PURPOSE[category]}."

        evidence = "Official documentation URL retrieved; classification remains to be verified"
        confidence = Confidence.LOW
        if page["status"] == "ok":
            text = page["text"].lower()
            evidence = f"Official page returned successfully: {page['title'] or 'documentation page'}"
            confidence = Confidence.LOW
            if "rest api" in text or "restful" in text:
                rest = "Yes"
                breadth = "Public REST API; breadth requires verification"
            if "graphql" in text:
                graphql = "Yes"
            if "mcp" in text:
                if "official" in text or "model context protocol" in text:
                    official_mcp = "Requires Verification"
            auth = KNOWN_AUTH.get(name, auth)

        known_no_api = {"Mermaid CLI","Sherlock"}
        if name in known_no_api:
            rest = "No public API"
            graphql = "No"
            breadth = "Command-line tool; no REST API classification"
            buildability = "Buildable as local CLI integration"
            blocker = "No hosted API; wrap CLI or provide a local execution adapter"
        elif auth != "Unknown":
            buildability = "Requires verification"
            blocker = "Authentication and account plan details require confirmation"
        else:
            buildability = "Requires Research"
            blocker = "Official API, authentication, account, and MCP documentation must be verified"

        if name == "Mermaid CLI":
            access = "Self-serve"
            official_mcp = "No known official MCP"
            community_mcp = "Unknown"

        return ResearchFinding(
            rank=app["rank"], app=name, category=category, description=description,
            what_it_does=description, auth_methods=auth, public_rest_api=rest,
            graphql_api=graphql, api_breadth=breadth, access=access,
            official_mcp=official_mcp, community_mcp=community_mcp,
            buildability=buildability, main_blocker=blocker,
            evidence_url=url, evidence=evidence, confidence=confidence,
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
    records.sort(key=lambda r:r["rank"])
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

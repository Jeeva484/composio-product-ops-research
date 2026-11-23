from datetime import date
from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"

def load_project_environment():
    """Load project env without replacing a valid process environment value."""
    load_dotenv(ENV_FILE, override=False)
    process_key = os.getenv("COMPOSIO_API_KEY", "")
    if not process_key.strip():
        load_dotenv(ENV_FILE, override=True)


load_project_environment()

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))
REQUEST_RETRIES = int(os.getenv("REQUEST_RETRIES", "3"))
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY", "")
COMPOSIO_USER_ID = os.getenv("COMPOSIO_USER_ID", "composio-product-ops-demo")
RESEARCH_DATE = date.today().isoformat()

"""Small, genuine Composio SDK integration for a Tool Router MCP session."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import COMPOSIO_USER_ID, ENV_FILE, load_project_environment


PLACEHOLDER_VALUES = {
    "",
    "PASTE_YOUR_NEW_PROJECT_KEY_HERE",
}
STATE_FILE = ROOT / ".composio_state.json"
RESULT_FILE = ROOT / "composio_github_result.json"


def get_composio_api_key():
    load_project_environment()
    key = os.getenv("COMPOSIO_API_KEY", "").strip()
    if key in PLACEHOLDER_VALUES:
        return ""
    return key


def key_diagnostic():
    key = get_composio_api_key()
    return {
        "api_key_configured": bool(key),
        "api_key_character_count": len(key),
    }


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    STATE_FILE.chmod(0o600)


def read_state() -> dict:
    if not STATE_FILE.exists():
        raise RuntimeError("No saved Composio session. Run --authorize-github first.")
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def load_session():
    from composio import Composio

    state = read_state()
    composio = Composio(api_key=get_composio_api_key())
    return composio, composio.sessions.use(state["session_id"], mcp=True), state


def sdk_status() -> dict:
    diagnostic = key_diagnostic()
    try:
        import composio
        from composio import Composio
    except ImportError as exc:
        return {
            "sdk_installed": False,
            "sdk_imported": False,
            **diagnostic,
            "session_created": False,
            "mcp_connection_established": False,
            "error": str(exc),
        }

    return {
        "sdk_installed": True,
        "sdk_imported": True,
        "sdk_version": getattr(composio, "__version__", "installed; version attribute unavailable"),
        **diagnostic,
        "session_created": False,
        "mcp_connection_established": False,
    }


def create_session(toolkit: str = "github") -> dict:
    status = sdk_status()
    if not status["sdk_installed"]:
        raise RuntimeError("Official Composio SDK is not installed")
    api_key = get_composio_api_key()
    if not api_key:
        return {
            **status,
            "session_created": False,
            "mcp_connection_established": False,
            "error": "COMPOSIO_API_KEY is missing or unset in the project .env and process environment",
        }

    from composio import Composio
    from composio_client._exceptions import AuthenticationError

    composio = Composio(api_key=api_key)
    try:
        session = composio.sessions.create(
            user_id=COMPOSIO_USER_ID,
            toolkits=[toolkit],
            manage_connections=True,
            mcp=True,
        )
    except AuthenticationError as exc:
        return {
            **status,
            "session_created": False,
            "mcp_connection_established": False,
            "error": "Composio returned HTTP 401 Invalid API key",
            "action": "Copy a valid project key from Platform -> project -> Getting Started -> Step 1",
            "sdk_error_type": type(exc).__name__,
        }

    mcp = getattr(session, "mcp", None)
    mcp_summary = {}
    if mcp is not None:
        if hasattr(mcp, "model_dump"):
            mcp_summary = mcp.model_dump(exclude={"headers", "authorization"})
        elif isinstance(mcp, dict):
            mcp_summary = {k: v for k, v in mcp.items() if k not in {"headers", "authorization"}}
        else:
            for key in ("url", "server_url", "type", "transport"):
                value = getattr(mcp, key, None)
                if value is not None:
                    mcp_summary[key] = str(value)

    result = {
        **status,
        "session_created": True,
        "session_id": getattr(session, "session_id", "returned"),
        "mcp_connection_established": False,
        "mcp_config_generated": bool(mcp_summary),
        "mcp_summary": mcp_summary,
        "toolkit": toolkit,
        "user_id": COMPOSIO_USER_ID,
        "note": "The SDK created a session and MCP configuration. This process does not itself connect an MCP client.",
    }
    return result


def authorize_github() -> dict:
    status = sdk_status()
    if not status["sdk_installed"]:
        raise RuntimeError("Official Composio SDK is not installed")
    if not get_composio_api_key():
        raise RuntimeError("COMPOSIO_API_KEY is missing from the project .env and process environment")

    from composio import Composio
    composio = Composio(api_key=get_composio_api_key())
    session = composio.sessions.create(
        user_id=COMPOSIO_USER_ID,
        toolkits=["github"],
        manage_connections=True,
        mcp=True,
    )
    connection = session.authorize("github")
    if not connection.redirect_url:
        raise RuntimeError("Composio did not return a GitHub authorization URL")

    state = {
        "session_id": session.session_id,
        "user_id": COMPOSIO_USER_ID,
        "toolkit": "github",
        "connection_request_id": connection.id,
    }
    save_state(state)
    return {
        "session_created": True,
        "session_id": session.session_id,
        "authorization_started": True,
        "authorization_url": connection.redirect_url,
        "mcp_connection_established": False,
        "next_step": "Complete GitHub authorization in the browser, then run --list-repositories",
    }


def _read_only_candidate(session) -> tuple[str, dict]:
    response = session.search(
        query="List repositories accessible to the currently authenticated GitHub user. Read-only. Return repository names."
    )
    schemas = getattr(response, "tool_schemas", {}) or {}
    candidates = []
    for slug, schema in schemas.items():
        normalized = slug.lower()
        description = str(getattr(schema, "description", "")).lower()
        combined = f"{normalized} {description}"
        if not any(word in combined for word in ("repository", "repositories", "repo")) or not any(word in combined for word in ("list", "get", "search")):
            continue
        if any(word in normalized for word in ("create", "delete", "update", "push", "write", "add")):
            continue
        input_schema = getattr(schema, "input_schema", {}) or {}
        candidates.append((slug, schema, input_schema, combined))
    if not candidates:
        raise RuntimeError("Composio search returned no suitable read-only repository-listing tool")
    candidates.sort(key=lambda item: (
        0 if "list" in item[0].lower() and "repos" in item[0].lower() else 1,
        0 if "list" in item[3] else 1,
    ))
    slug, schema, input_schema, _ = candidates[0]
    return slug, input_schema


def _arguments_for_five(input_schema: Any) -> dict:
    if hasattr(input_schema, "model_dump"):
        input_schema = input_schema.model_dump()
    if not isinstance(input_schema, dict):
        return {}
    properties = input_schema.get("properties", {})
    args = {}
    for key in ("per_page", "limit", "page_size", "first"):
        if key in properties:
            args[key] = 5
            break
    for key in ("page", "page_number"):
        if key in properties:
            args[key] = 1
    return args


def _names_from_payload(payload: Any) -> list[str]:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return []
    if isinstance(payload, list):
        names = []
        for item in payload:
            if isinstance(item, dict):
                name = item.get("full_name") or item.get("name")
                if name:
                    names.append(str(name))
        return names[:5]
    if isinstance(payload, dict):
        for key in ("repositories", "repos", "items", "data"):
            if key in payload:
                names = _names_from_payload(payload[key])
                if names:
                    return names[:5]
        name = payload.get("full_name") or payload.get("name")
        return [str(name)] if name else []
    return []


def list_github_repositories() -> dict:
    if not get_composio_api_key():
        raise RuntimeError("COMPOSIO_API_KEY is missing from the project .env and process environment")
    _, session, state = load_session()
    connection_states = session.toolkits(toolkits=["github"])
    github_state = next((item for item in connection_states.items if item.slug.lower() == "github"), None)
    if not github_state or not github_state.connection or not github_state.connection.is_active:
        return {
            "connected": False,
            "toolkit": "github",
            "message": "GitHub authorization is not active. Complete the authorization URL before retrying.",
        }

    tool_slug, input_schema = _read_only_candidate(session)
    result = session.execute(tool_slug, arguments=_arguments_for_five(input_schema))
    result_type = getattr(result, "result_type", None)
    payload = getattr(result, "data", None)
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump(mode="json")
    elif not isinstance(payload, (str, dict, list, type(None))):
        payload = str(payload)

    captured = {
        "toolkit": "github",
        "tool_slug": tool_slug,
        "result_type": result_type,
        "log_id": getattr(result, "log_id", None),
        "provider_response": payload,
        "session_id": state["session_id"],
    }
    RESULT_FILE.write_text(json.dumps(captured, indent=2, default=str), encoding="utf-8")
    RESULT_FILE.chmod(0o600)

    if result_type != "completed":
        return {
            "connected": True,
            "tool_slug": tool_slug,
            "result_type": result_type,
            "log_id": getattr(result, "log_id", None),
            "error": getattr(result, "error", None),
            "captured_response_file": str(RESULT_FILE),
        }
    return {
        "connected": True,
        "toolkit": "github",
        "tool_slug": tool_slug,
        "repository_names": _names_from_payload(payload),
        "log_id": getattr(result, "log_id", None),
        "result_type": result_type,
        "captured_response_file": str(RESULT_FILE),
        "mcp_connection_established": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Test the official Composio SDK integration")
    parser.add_argument("--status", action="store_true", help="Report local SDK status")
    parser.add_argument("--create-session", action="store_true", help="Create a real Composio session")
    parser.add_argument("--authorize-github", action="store_true", help="Create a session and start GitHub OAuth")
    parser.add_argument("--list-repositories", action="store_true", help="List up to five GitHub repositories read-only")
    parser.add_argument("--toolkit", default="github", help="Toolkit for the session")
    args = parser.parse_args()

    if args.status:
        result = sdk_status()
    elif args.create_session:
        result = create_session(args.toolkit)
    elif args.authorize_github:
        result = authorize_github()
    elif args.list_repositories:
        result = list_github_repositories()
    else:
        parser.error("Choose --status, --create-session, --authorize-github, or --list-repositories")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

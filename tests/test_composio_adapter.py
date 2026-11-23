import agent.composio_adapter as adapter
import config.settings as settings


def test_sdk_status_is_real_and_reports_missing_key(tmp_path, monkeypatch):
    monkeypatch.delenv("COMPOSIO_API_KEY", raising=False)
    monkeypatch.setattr(settings, "ENV_FILE", tmp_path / "missing.env")
    status = adapter.sdk_status()
    assert status["sdk_installed"] is True
    assert status["sdk_imported"] is True
    assert status["api_key_configured"] is False
    assert status["session_created"] is False
    assert status["mcp_connection_established"] is False


def test_create_session_stops_cleanly_without_key(tmp_path, monkeypatch):
    monkeypatch.delenv("COMPOSIO_API_KEY", raising=False)
    monkeypatch.setattr(settings, "ENV_FILE", tmp_path / "missing.env")
    result = adapter.create_session("github")
    assert result["session_created"] is False
    assert result["mcp_connection_established"] is False
    assert "COMPOSIO_API_KEY" in result["error"]


def test_project_env_is_loaded_relative_to_project(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("COMPOSIO_API_KEY=ak_test_project_key\n")
    monkeypatch.delenv("COMPOSIO_API_KEY", raising=False)
    monkeypatch.setattr(settings, "ENV_FILE", env_file)
    settings.load_project_environment()
    assert adapter.get_composio_api_key() == "ak_test_project_key"


def test_valid_process_key_is_not_overwritten_by_empty_env(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("COMPOSIO_API_KEY=\n")
    monkeypatch.setenv("COMPOSIO_API_KEY", "ak_valid_inline_key")
    monkeypatch.setattr(settings, "ENV_FILE", env_file)
    settings.load_project_environment()
    assert adapter.get_composio_api_key() == "ak_valid_inline_key"


def test_repository_name_extraction_caps_at_five():
    payload = {"repositories": [{"full_name": f"owner/repo-{i}"} for i in range(8)]}
    assert adapter._names_from_payload(payload) == [f"owner/repo-{i}" for i in range(5)]


def test_tool_candidate_rejects_mutation_tools():
    class Schema:
        def __init__(self, description, input_schema=None):
            self.description = description
            self.input_schema = input_schema or {"properties": {}}

    class Response:
        tool_schemas = {
            "GITHUB_DELETE_REPOSITORY": Schema("Delete repository"),
            "GITHUB_LIST_REPOSITORIES": Schema(
                "List repositories accessible to the authenticated user",
                {"properties": {"per_page": {"type": "integer"}}},
            ),
        }

    class Session:
        def search(self, **kwargs):
            return Response()

    slug, schema = adapter._read_only_candidate(Session())
    assert slug == "GITHUB_LIST_REPOSITORIES"
    assert adapter._arguments_for_five(schema) == {"per_page": 5}

import tempfile
from agent.exporter import export_findings
from agent.models import ResearchFinding

def test_exporter_writes_json_and_csv():
    finding = ResearchFinding(
        rank=1, app="Test App", category="CRM and Sales",
        description="Test description", what_it_does="Test workflow",
        evidence_url="https://example.com/docs", evidence="Test evidence",
        last_researched="2026-11-23",
    )
    with tempfile.TemporaryDirectory() as directory:
        json_path, csv_path = export_findings([finding], directory)
        assert json_path.exists()
        assert csv_path.exists()

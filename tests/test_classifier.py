import json
from agent.classifier import summarize

def test_classifier_uses_actual_dataset():
    rows = json.load(open("data/research_results.json"))
    result = summarize(rows)
    assert sum(result["access"].values()) == 100
    assert sum(result["auth"].values()) == 100
    assert len(result["categories"]) == 10

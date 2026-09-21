from pathlib import Path

from audit_agent.tools import detect_anomalies, evaluate_finance_controls, summarize_transactions


DATA = Path(__file__).resolve().parents[1] / "data" / "sample_transactions.csv"


def test_summary_counts_population():
    summary = summarize_transactions(str(DATA))
    assert summary["transaction_count"] == 8
    assert summary["max_absolute_value"] == 125000.0


def test_anomalies_include_duplicate_and_missing_approver():
    findings = detect_anomalies(str(DATA))
    by_id = {item["transaction_id"]: item for item in findings}
    assert "possible_duplicate_invoice" in by_id["TX001"]["reasons"]
    assert "possible_duplicate_invoice" in by_id["TX002"]["reasons"]
    assert "missing_approver" in by_id["TX003"]["reasons"]


def test_control_testing_identifies_key_failures():
    result = evaluate_finance_controls(str(DATA))
    controls = [f["control"] for f in result["failures"]]
    assert "approval_required" in controls
    assert "segregation_of_duties" in controls
    assert "duplicate_invoice_prevention" in controls

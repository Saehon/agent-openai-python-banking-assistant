from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


def _read_transactions(csv_path: str) -> list[dict[str, Any]]:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Transaction file not found: {csv_path}")

    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"transaction_id", "date", "vendor", "amount", "currency", "account", "preparer", "approver", "invoice_id"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

        for raw in reader:
            row = dict(raw)
            try:
                row["amount"] = float(row["amount"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid amount for transaction {row.get('transaction_id')}") from exc
            rows.append(row)
    return rows


def summarize_transactions(csv_path: str) -> dict[str, Any]:
    """Return audit-oriented population statistics for a transaction CSV."""
    rows = _read_transactions(csv_path)
    amounts = [abs(float(r["amount"])) for r in rows]
    by_account: dict[str, float] = defaultdict(float)
    by_vendor: dict[str, float] = defaultdict(float)

    for row in rows:
        amount = float(row["amount"])
        by_account[row["account"]] += amount
        by_vendor[row["vendor"]] += amount

    return {
        "transaction_count": len(rows),
        "total_absolute_value": round(sum(amounts), 2),
        "mean_absolute_value": round(mean(amounts), 2) if amounts else 0.0,
        "max_absolute_value": round(max(amounts), 2) if amounts else 0.0,
        "top_accounts": sorted(by_account.items(), key=lambda x: abs(x[1]), reverse=True)[:5],
        "top_vendors": sorted(by_vendor.items(), key=lambda x: abs(x[1]), reverse=True)[:5],
    }


def detect_anomalies(
    csv_path: str,
    high_value_threshold: float = 50_000.0,
    z_threshold: float = 2.5,
) -> list[dict[str, Any]]:
    """Flag high-value, statistical, duplicate, weekend, round-dollar and approval anomalies."""
    rows = _read_transactions(csv_path)
    amounts = [abs(float(r["amount"])) for r in rows]
    mu = mean(amounts) if amounts else 0.0
    sigma = pstdev(amounts) if len(amounts) > 1 else 0.0

    duplicate_keys = Counter(
        (r["vendor"].strip().lower(), r["invoice_id"].strip().lower(), round(float(r["amount"]), 2))
        for r in rows
        if r["invoice_id"].strip()
    )

    findings: list[dict[str, Any]] = []
    for row in rows:
        amount = abs(float(row["amount"]))
        reasons: list[str] = []

        if amount >= high_value_threshold:
            reasons.append("high_value")

        if sigma > 0 and (amount - mu) / sigma >= z_threshold:
            reasons.append("statistical_outlier")

        key = (row["vendor"].strip().lower(), row["invoice_id"].strip().lower(), round(float(row["amount"]), 2))
        if row["invoice_id"].strip() and duplicate_keys[key] > 1:
            reasons.append("possible_duplicate_invoice")

        try:
            weekday = datetime.strptime(row["date"], "%Y-%m-%d").weekday()
            if weekday >= 5:
                reasons.append("weekend_posting")
        except ValueError:
            reasons.append("invalid_date")

        if amount >= 1_000 and math.isclose(amount % 1_000, 0.0, abs_tol=0.01):
            reasons.append("round_amount")

        if not row["approver"].strip():
            reasons.append("missing_approver")
        elif row["preparer"].strip().lower() == row["approver"].strip().lower():
            reasons.append("segregation_of_duties_conflict")

        if reasons:
            findings.append(
                {
                    "transaction_id": row["transaction_id"],
                    "vendor": row["vendor"],
                    "amount": float(row["amount"]),
                    "account": row["account"],
                    "reasons": reasons,
                    "risk_score": min(100, 15 * len(reasons) + (20 if "high_value" in reasons else 0)),
                }
            )

    return sorted(findings, key=lambda x: x["risk_score"], reverse=True)


def evaluate_finance_controls(
    csv_path: str,
    approval_threshold: float = 10_000.0,
) -> dict[str, Any]:
    """Test key finance controls over approvals, segregation of duties and duplicate invoices."""
    rows = _read_transactions(csv_path)
    failures: list[dict[str, Any]] = []
    seen_invoice: dict[tuple[str, str, float], str] = {}

    for row in rows:
        amount = abs(float(row["amount"]))
        tx_id = row["transaction_id"]
        approver = row["approver"].strip()
        preparer = row["preparer"].strip()

        if amount >= approval_threshold and not approver:
            failures.append({"transaction_id": tx_id, "control": "approval_required", "severity": "high"})
        if approver and preparer.lower() == approver.lower():
            failures.append({"transaction_id": tx_id, "control": "segregation_of_duties", "severity": "high"})

        invoice_id = row["invoice_id"].strip().lower()
        if invoice_id:
            key = (row["vendor"].strip().lower(), invoice_id, round(float(row["amount"]), 2))
            if key in seen_invoice:
                failures.append(
                    {
                        "transaction_id": tx_id,
                        "control": "duplicate_invoice_prevention",
                        "severity": "medium",
                        "related_transaction": seen_invoice[key],
                    }
                )
            else:
                seen_invoice[key] = tx_id

    tested = max(len(rows), 1)
    high_failures = sum(1 for f in failures if f["severity"] == "high")
    return {
        "population_size": len(rows),
        "failures": failures,
        "failure_count": len(failures),
        "high_severity_failures": high_failures,
        "control_exception_rate": round(len(failures) / tested, 4),
    }


def audit_plan(risk_area: str) -> dict[str, Any]:
    """Generate a deterministic audit-work-program skeleton for a finance/operations risk area."""
    key = risk_area.strip().lower()
    programs = {
        "revenue": ["revenue recognition", "cut-off", "contract terms", "credit notes", "manual journal entries"],
        "procurement": ["vendor onboarding", "purchase approvals", "three-way match", "duplicate payments", "conflicts of interest"],
        "payroll": ["joiner/mover/leaver", "master-data changes", "ghost employees", "overtime", "bank-account changes"],
        "treasury": ["bank access", "payment approvals", "reconciliations", "liquidity", "counterparty exposure"],
        "expenses": ["policy compliance", "approvals", "duplicates", "weekend/holiday spend", "merchant anomalies"],
    }
    scope = programs.get(key, ["governance", "process design", "access", "approvals", "reconciliation", "monitoring"])
    return {
        "risk_area": risk_area,
        "objectives": [
            "Assess whether governance and controls are suitably designed.",
            "Test whether key controls operated effectively over the selected population.",
            "Use data analytics to identify anomalous transactions and emerging risk patterns.",
            "Develop evidence-based findings with management implications and remediation actions.",
        ],
        "work_program": scope,
        "required_evidence": ["process narrative", "control matrix", "population extract", "supporting documents", "management response"],
        "human_gate": "Audit lead reviews scope, materiality, exceptions, and final conclusions before release.",
    }


def render_finding(findings_json: str) -> str:
    """Turn machine findings into a consistent audit-finding structure without making an autonomous final judgment."""
    payload = json.loads(findings_json)
    return json.dumps(
        {
            "condition": payload.get("condition", ""),
            "criteria": payload.get("criteria", ""),
            "cause": payload.get("cause", "Requires management validation"),
            "effect": payload.get("effect", "Potential financial, operational, compliance, or governance impact"),
            "recommendation": payload.get("recommendation", "Management to define and own remediation"),
            "evidence": payload.get("evidence", []),
            "human_review_required": True,
        },
        indent=2,
    )

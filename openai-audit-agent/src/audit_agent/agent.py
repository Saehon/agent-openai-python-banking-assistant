from __future__ import annotations

import os

from agents import Agent
from agents.decorators import tool

from .tools import audit_plan, detect_anomalies, evaluate_finance_controls, render_finding, summarize_transactions


@tool
def transaction_summary(csv_path: str) -> dict:
    """Summarize a transaction population for audit scoping."""
    return summarize_transactions(csv_path)


@tool
def anomaly_scan(csv_path: str, high_value_threshold: float = 50_000.0, z_threshold: float = 2.5) -> list[dict]:
    """Scan transactions for audit-relevant anomalies and return ranked exceptions."""
    return detect_anomalies(csv_path, high_value_threshold, z_threshold)


@tool
def control_test(csv_path: str, approval_threshold: float = 10_000.0) -> dict:
    """Test approval, segregation-of-duties, and duplicate-invoice controls."""
    return evaluate_finance_controls(csv_path, approval_threshold)


@tool
def build_work_program(risk_area: str) -> dict:
    """Create an audit work-program skeleton for a finance or operations risk area."""
    return audit_plan(risk_area)


@tool
def structure_finding(findings_json: str) -> str:
    """Structure evidence into an audit finding that remains subject to human review."""
    return render_finding(findings_json)


def build_audit_leader_agent() -> Agent:
    model = os.getenv("OPENAI_MODEL", "gpt-5.6")

    risk_agent = Agent(
        name="Risk & Scoping Specialist",
        model=model,
        instructions=(
            "You are an internal-audit risk and scoping specialist. Identify material finance and operations risks, "
            "define audit objectives, connect risks to evidence, and avoid unsupported conclusions. Use the work-program "
            "tool when it improves specificity. Escalate materiality and scope decisions to the human audit lead."
        ),
        tools=[build_work_program, transaction_summary],
    )

    forensic_agent = Agent(
        name="Forensic Analytics Specialist",
        model=model,
        instructions=(
            "You are a forensic accounting and transaction-analytics specialist. Use population-level analytics to surface "
            "unusual transactions, duplicate indicators, approval gaps, weekend postings, round amounts, and statistical outliers. "
            "Treat analytics as risk indicators, not proof of misconduct. Cite transaction IDs and evidence returned by tools."
        ),
        tools=[transaction_summary, anomaly_scan],
    )

    controls_agent = Agent(
        name="Controls Testing Specialist",
        model=model,
        instructions=(
            "You test finance controls over approvals, segregation of duties, duplicate invoices, and related process controls. "
            "Separate design observations from operating-effectiveness exceptions. Do not infer control failure beyond the evidence."
        ),
        tools=[control_test, transaction_summary],
    )

    reporting_agent = Agent(
        name="Audit Reporting & Governance Specialist",
        model=model,
        instructions=(
            "You translate validated audit evidence into concise executive-ready observations. Distinguish fact, inference, and "
            "management assertion. Use condition/criteria/cause/effect/recommendation structure when useful. Every final issue must "
            "state that human audit-lead review is required before release."
        ),
        tools=[structure_finding],
    )

    return Agent(
        name="Finance & Operations Audit Leader Agent",
        model=model,
        instructions=(
            "Act as the coordinating internal-audit agent for finance, accounting, and business operations. Your workflow is: "
            "(1) understand objective and scope; (2) ask the Risk & Scoping Specialist for a risk-based plan when needed; "
            "(3) delegate population analytics to the Forensic Analytics Specialist; (4) delegate control testing to the Controls "
            "Testing Specialist; (5) use the Reporting & Governance Specialist to structure validated findings; and (6) present an "
            "evidence register, unresolved questions, practical remediation options, and a HUMAN AUDIT LEAD GATE. Never characterize "
            "an anomaly as fraud without corroborating evidence. Never make an autonomous disciplinary, regulatory, or financial-"
            "reporting conclusion. Preserve audit independence and clearly label assumptions."
        ),
        tools=[
            risk_agent.as_tool(
                tool_name="risk_and_scoping_review",
                tool_description="Develop risk assessment, audit scope, objectives and evidence plan.",
            ),
            forensic_agent.as_tool(
                tool_name="forensic_analytics_review",
                tool_description="Analyze transaction populations for anomalous or potentially irregular patterns.",
            ),
            controls_agent.as_tool(
                tool_name="controls_testing_review",
                tool_description="Evaluate finance control exceptions from transaction evidence.",
            ),
            reporting_agent.as_tool(
                tool_name="audit_reporting_review",
                tool_description="Structure validated observations for executive and governance reporting.",
            ),
        ],
    )

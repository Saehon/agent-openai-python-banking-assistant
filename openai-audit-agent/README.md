# Finance & Operations Audit Leader Agent

A portfolio-grade internal-audit prototype built with the **OpenAI Agents SDK**. It adapts the multi-agent orchestration pattern already present in this repository to a finance, accounting, operations, controls, and forensic-audit use case.

## Why this exists

The prototype is designed around a modern internal-audit operating model:

- risk-based audit scoping and work-program design;
- finance and accounting control testing;
- transaction-level anomaly detection and forensic triage;
- evidence-based reporting for management and governance bodies;
- explicit human review before any final audit conclusion.

Analytics identify **risk indicators, not proof of fraud**. Materiality, misconduct, regulatory, disciplinary, and financial-reporting conclusions remain human decisions.

## Architecture

```text
                    Finance & Operations Audit Leader
                                  |
          +-----------------------+-----------------------+
          |                       |                       |
 Risk & Scoping          Forensic Analytics        Controls Testing
 Specialist              Specialist                Specialist
          \                       |                       /
           \----------------------|----------------------/
                                  |
                    Audit Reporting & Governance
                                  |
                         HUMAN AUDIT LEAD GATE
```

The coordinator uses specialist agents as tools. Local Python tools provide deterministic transaction analytics and control tests, while the LLM performs scoping, synthesis, questioning, and evidence-based explanation.

## Included capabilities

| Capability | What the prototype does |
|---|---|
| Risk assessment | Builds objectives, scope, work program, evidence requirements |
| Population analytics | Summarizes transaction populations and concentration |
| Forensic triage | Flags high-value, duplicate, weekend, round-dollar, approval and statistical anomalies |
| Controls testing | Tests approvals, segregation of duties and duplicate-invoice prevention |
| Reporting | Structures findings and separates evidence from inference |
| Governance | Requires a human audit-lead gate before final release |

## Quick start

```bash
cd openai-audit-agent
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
export OPENAI_API_KEY="..."

audit-agent "Perform an initial finance audit risk assessment and analyze the sample population" \
  --csv data/sample_transactions.csv
```

You may set `OPENAI_MODEL` to any OpenAI model available to your API project. The default is `gpt-5.6`.

## Example audit prompt

```text
Review the transaction population for procurement and expense risks. Identify the highest-priority exceptions, test approval and segregation-of-duties controls, distinguish indicators from confirmed issues, and prepare an executive audit summary with an evidence register and unresolved questions.
```

## Data contract

The CSV tools expect these columns:

```text
transaction_id,date,vendor,amount,currency,account,preparer,approver,invoice_id
```

The included sample data are synthetic and safe for demonstration.

## Design principles

1. **Evidence first** — transaction IDs and deterministic test results support every exception.
2. **Human decision rights** — the agent does not autonomously conclude fraud, misconduct, material misstatement, or regulatory breach.
3. **Audit independence** — management explanations are treated as assertions until corroborated.
4. **Population analytics** — testing can operate over full CSV populations instead of only samples.
5. **Extensible integration** — the next step is to expose AuditData-API or ERP extracts as MCP tools rather than reading local CSV files.

## Next integration targets

- `Saehon/AuditData-API` for standardized GL, trial-balance, AR, AP and inventory data access.
- ERP / finance-system APIs through MCP.
- Continuous control monitoring and scheduled exception analysis.
- Evidence-store / working-paper integration with immutable audit logs.
- Evaluation datasets for false positives, exception precision, reviewer agreement and remediation outcomes.

## Tests

```bash
pip install -e '.[dev]'
pytest
```

## Status

Prototype for research, portfolio demonstration, and controlled testing. It is not a replacement for professional judgment or an organization's approved audit methodology.

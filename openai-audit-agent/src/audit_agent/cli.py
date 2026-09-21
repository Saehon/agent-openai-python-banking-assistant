from __future__ import annotations

import argparse

from agents import Runner

from .agent import build_audit_leader_agent


def main() -> None:
    parser = argparse.ArgumentParser(description="Finance & Operations Audit Leader Agent")
    parser.add_argument("prompt", help="Audit question or task")
    parser.add_argument("--csv", dest="csv_path", help="Optional transaction CSV path")
    args = parser.parse_args()

    prompt = args.prompt
    if args.csv_path:
        prompt += f"\nUse this transaction population when relevant: {args.csv_path}"

    result = Runner.run_sync(build_audit_leader_agent(), prompt)
    print(result.final_output)


if __name__ == "__main__":
    main()

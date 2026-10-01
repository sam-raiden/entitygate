"""Runs all three methods over every case in cases/, prints a scorecard.

Usage (from the repo root):
    python -m dotenv run -- python benchmark/run_benchmark.py
  or just make sure GROQ_API_KEY is set in the environment first.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmark.methods import entitygate_check, faithfulness_check, naive_llm  # noqa: E402

_CASES_DIR = Path(__file__).resolve().parent / "cases"


def load_cases() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(_CASES_DIR.glob("*.json"))]


def run() -> None:
    cases = load_cases()
    rows = []
    for case in cases:
        is_misattributed = case["ground_truth"] == "misattributed"
        naive = naive_llm(case)
        faith = faithfulness_check(case)
        gate = entitygate_check(case)
        rows.append({
            "case": case["id"],
            "ground_truth": case["ground_truth"],
            "naive_accepted": naive.accepted,
            "naive_correct": naive.accepted != is_misattributed,
            "faithfulness_accepted": faith.accepted,
            "faithfulness_correct": faith.accepted != is_misattributed,
            "entitygate_accepted": gate.accepted,
            "entitygate_correct": gate.accepted != is_misattributed,
            "entitygate_reason": gate.raw,
        })

    print(f"\n{'case':<30} {'truth':<14} {'naive':<10} {'faithful':<10} {'entitygate':<12} reason")
    print("-" * 100)
    for r in rows:
        print(
            f"{r['case']:<30} {r['ground_truth']:<14} "
            f"{'ACCEPT' if r['naive_accepted'] else 'reject':<10} "
            f"{'ACCEPT' if r['faithfulness_accepted'] else 'reject':<10} "
            f"{'ACCEPT' if r['entitygate_accepted'] else 'reject':<12} {r['entitygate_reason']}"
        )

    misattr_rows = [r for r in rows if r["ground_truth"] == "misattributed"]
    correct_rows = [r for r in rows if r["ground_truth"] == "correct"]

    def rate(rows_, key):
        return f"{sum(1 for r in rows_ if r[key]) }/{len(rows_)}" if rows_ else "n/a"

    print("\n--- Scorecard ---")
    print(f"Misattribution cases correctly REJECTED (higher = better):")
    print(f"  naive:        {rate(misattr_rows, 'naive_correct')}")
    print(f"  faithfulness: {rate(misattr_rows, 'faithfulness_correct')}")
    print(f"  entitygate:   {rate(misattr_rows, 'entitygate_correct')}")
    print(f"\nGenuinely correct cases ACCEPTED (higher = better -- the false-negative cost):")
    print(f"  naive:        {rate(correct_rows, 'naive_correct')}")
    print(f"  faithfulness: {rate(correct_rows, 'faithfulness_correct')}")
    print(f"  entitygate:   {rate(correct_rows, 'entitygate_correct')}")

    out_path = Path(__file__).resolve().parent / "results" / "latest.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nFull results written to {out_path}")


if __name__ == "__main__":
    run()

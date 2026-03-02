#!/usr/bin/env python3
"""Pipeline orchestrator: runs all marketing agent steps for one or all customers.

Steps (per customer):
  0. /0-load-data      - refresh data_cache.json (once, before any customer)
  1. /1-analyze         - detect triggers, infer intent
  2. /2-guardrail       - check blocking conditions
  3. /3-offer           - recommend product offer
  4. /4-content         - generate marketing content
  5. /5-legal           - legal compliance
  6. /6-brand           - brand compliance
  F. /9-flush-output    - append cached rows to Google Sheet
"""

import json
import os
import subprocess
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SKILLS_DIR = os.path.join(PROJECT_ROOT, ".claude", "skills")
DATA_CACHE = os.path.join(PROJECT_ROOT, "data_cache.json")

STEPS = [
    "1-analyze",
    "2-guardrail",
    "3-offer",
    "4-content",
    "5-legal",
    "6-brand",
]


def run_step(step_name: str, arg: str) -> bool:
    """Run a single step's run.py with the given argument. Returns True on success."""
    script = os.path.join(SKILLS_DIR, step_name, "run.py")
    if not os.path.isfile(script):
        print(f"  [SKIP] {step_name}: run.py not found")
        return False
    print(f"\n{'='*60}")
    print(f"  STEP: {step_name}  |  arg: {arg}")
    print(f"{'='*60}")
    result = subprocess.run(
        [sys.executable, script, arg],
        cwd=PROJECT_ROOT,
    )
    if result.returncode != 0:
        print(f"  [ERROR] {step_name} exited with code {result.returncode}")
        return False
    return True


def get_all_customer_ids() -> list[str]:
    """Read customer IDs from the data cache."""
    with open(DATA_CACHE, encoding="utf-8") as f:
        cache = json.load(f)
    customers = cache.get("all_customers", [])
    return [c["customer_id"] for c in customers if "customer_id" in c]


def run_pipeline_for_customer(cid: str) -> bool:
    """Execute the full pipeline for a single customer. Returns True if all steps passed."""
    print(f"\n{'#'*60}")
    print(f"  PIPELINE START: {cid}")
    print(f"{'#'*60}")

    all_ok = True

    for step in STEPS:
        ok = run_step(step, cid)
        if not ok:
            all_ok = False

    status = "OK" if all_ok else "PARTIAL"
    print(f"\n  PIPELINE {status}: {cid}")
    return all_ok


def main():
    if len(sys.argv) < 2:
        print("Usage: run.py <customer_id | all>")
        sys.exit(1)

    target = sys.argv[1].strip()

    # Step 0: Always load data first
    print("=" * 60)
    print("  STEP 0: load-data")
    print("=" * 60)
    ok = run_step("0-load-data", "")
    if not ok:
        print("FATAL: load-data failed. Aborting pipeline.")
        sys.exit(1)

    if target.lower() == "all":
        customer_ids = get_all_customer_ids()
        print(f"\nProcessing ALL {len(customer_ids)} customers: {', '.join(customer_ids)}")
        results = {}
        for cid in customer_ids:
            results[cid] = run_pipeline_for_customer(cid)

        # Flush all at once
        print(f"\n{'='*60}")
        print("  FLUSH: writing all results to Google Sheet")
        print(f"{'='*60}")
        run_step("9-flush-output", "all")

        # Summary
        passed = sum(1 for v in results.values() if v)
        failed = len(results) - passed
        print(f"\n{'#'*60}")
        print(f"  PIPELINE SUMMARY")
        print(f"  Total: {len(results)}  |  OK: {passed}  |  Partial: {failed}")
        for cid, ok in results.items():
            print(f"    {cid}: {'OK' if ok else 'PARTIAL'}")
        print(f"{'#'*60}")
    else:
        run_pipeline_for_customer(target)

        # Flush single customer
        print(f"\n{'='*60}")
        print(f"  FLUSH: writing {target} results to Google Sheet")
        print(f"{'='*60}")
        run_step("9-flush-output", target)

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()

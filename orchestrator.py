#!/usr/bin/env python3
"""
Simple Python orchestrator for telecom marketing agent skills.

This script replaces the need to invoke skills via Claude.
It works directly with the existing `.claude/skills/*/run.py` scripts.

Usage examples (from project root, where `CLAUDE.md` lives):

  # Run a single skill
  python3 orchestrator.py 0-load-data
  python3 orchestrator.py 1-analyze C005

  # Run the full pipeline for one customer
  python3 orchestrator.py 8-pipeline C005

  # Run the full pipeline for all customers
  python3 orchestrator.py 8-pipeline all

Skills supported (mirrors `CLAUDE.md`):
  - 0-load-data
  - 1-analyze
  - 2-guardrail
  - 3-offer
  - 4-content
  - 5-legal
  - 6-brand
  - 7-visualize
  - 8-pipeline
  - 9-flush-output
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from typing import List


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(PROJECT_ROOT, ".claude", "skills")
PYTHON = sys.executable or "python3"


SKILL_NAMES = [
    "0-load-data",
    "1-analyze",
    "2-guardrail",
    "3-offer",
    "4-content",
    "5-legal",
    "6-brand",
    "7-visualize",
    "8-pipeline",
    "9-flush-output",
]


def run_subprocess(cmd: List[str]) -> int:
    """Run a subprocess, streaming output, and return its exit code."""
    print(f"\n$ {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130


def run_skill_direct(skill: str, arg: str | None) -> int:
    """
    Run a single skill's `run.py` directly.

    This is used for skills 0-7 and 9. For 8-pipeline we orchestrate steps ourselves.
    """
    skill_dir = os.path.join(SKILLS_DIR, skill)
    script_path = os.path.join(skill_dir, "run.py")

    if not os.path.exists(script_path):
        print(f"ERROR: {script_path} not found.")
        return 1

    cmd = [PYTHON, script_path]
    if arg is not None:
        cmd.append(arg)

    return run_subprocess(cmd)


def run_pipeline(target: str) -> int:
    """
    Implement `/8-pipeline` behavior without relying on Claude.

    - Always runs `/0-load-data` first.
    - Then runs the per-customer pipeline steps:
        1-analyze -> 2-guardrail -> 3-offer -> 4-content -> 5-legal -> 6-brand
    - Finally runs `/9-flush-output` with the same target.
    """
    print("=== PIPELINE START ===")

    # 0) Always refresh data cache
    print("\n[step 0] /0-load-data")
    code = run_skill_direct("0-load-data", None)
    if code != 0:
        print("Aborting pipeline: /0-load-data failed.")
        return code

    # 1) 1-analyze
    print("\n[step 1] /1-analyze")
    code = run_skill_direct("1-analyze", target)
    if code != 0:
        print("Aborting pipeline: /1-analyze failed.")
        return code

    # 2) 2-guardrail
    print("\n[step 2] /2-guardrail")
    code = run_skill_direct("2-guardrail", target)
    if code != 0:
        print("Aborting pipeline: /2-guardrail failed.")
        return code

    # 3) 3-offer
    print("\n[step 3] /3-offer")
    code = run_skill_direct("3-offer", target)
    if code != 0:
        print("Aborting pipeline: /3-offer failed.")
        return code

    # 4) 4-content
    print("\n[step 4] /4-content")
    code = run_skill_direct("4-content", target)
    if code != 0:
        print("Aborting pipeline: /4-content failed.")
        return code

    # 5) 5-legal
    print("\n[step 5] /5-legal")
    code = run_skill_direct("5-legal", target)
    if code != 0:
        print("Aborting pipeline: /5-legal failed.")
        return code

    # 6) 6-brand
    print("\n[step 6] /6-brand")
    code = run_skill_direct("6-brand", target)
    if code != 0:
        print("Aborting pipeline: /6-brand failed.")
        return code

    # 7) Flush to Google Sheets
    print("\n[final] /9-flush-output")
    code = run_skill_direct("9-flush-output", target)
    if code != 0:
        print("Pipeline finished with errors during /9-flush-output.")
        return code

    print("\n=== PIPELINE DONE ===")
    return 0


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Python orchestrator for telecom marketing agent skills (no Claude required)."
    )
    parser.add_argument(
        "skill",
        help="Skill to run (e.g. 0-load-data, 1-analyze, 8-pipeline, 9-flush-output).",
    )
    parser.add_argument(
        "argument",
        nargs="?",
        help="Optional argument for the skill (e.g. customer ID like C005 or 'all').",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available skills and exit.",
    )
    return parser.parse_args(argv)


def list_skills() -> None:
    print("Available skills:")
    for name in SKILL_NAMES:
        print(f"  - {name}")


def main(argv: List[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # Special-case: just list skills
    if "--list" in argv and len(argv) == 1:
        list_skills()
        return 0

    args = parse_args(argv)

    if args.list:
        list_skills()

    skill = args.skill
    if skill not in SKILL_NAMES:
        print(f"ERROR: Unknown skill '{skill}'.")
        list_skills()
        return 1

    # Normalize argument: many skills expect either a customer ID or 'all'.
    arg = args.argument

    if skill == "8-pipeline":
        if arg is None:
            print("ERROR: /8-pipeline requires an argument (customer ID like C005 or 'all').")
            return 1
        return run_pipeline(arg)

    # All other skills: just delegate to their run.py
    return run_skill_direct(skill, arg)


if __name__ == "__main__":
    raise SystemExit(main())

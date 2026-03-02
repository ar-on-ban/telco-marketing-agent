---
name: 8-pipeline
description: Run the full marketing agent pipeline for one or all customers
---

## Input
- Argument: $ARGUMENTS
  - Single customer ID (e.g., `C001`) -> process one customer
  - `all` -> process all customers from "customer_data" worksheet

## Task

### Mode 1: Single Customer
If $ARGUMENTS is a customer ID, run all skills in sequence for that customer.

### Mode 2: All Customers
If $ARGUMENTS is `all`:
1. Read all customer IDs from "customer_data" worksheet
2. For each customer, run the full pipeline
3. Print a final summary with totals

## Pipeline Execution Strategy

ALWAYS start with `/0-load-data` so that `data_cache.json` is refreshed before any per-customer steps. All per-step skills manage their own `.claude/skills/<step>/run.py` scripts as follows:

- If a step's `run.py` already exists, it is run directly (no additional natural-language instructions).
- If a step's `run.py` is missing or its `SKILL.md` body has changed compared to `SKILL-backup.md`, the step regenerates `run.py`, refreshes `SKILL-backup.md`, then runs the updated script.

## Pipeline Steps (per customer) in order

0. **/0-load-data**
1. **/1-analyze**
2. **/2-guardrail**
3. **/3-offer**
4. **/4-content**
5. **/5-legal**
6. **/6-brand**

## Execution details

Work relative to the project root where `CLAUDE.md` lives.

1. **When invoked as a Claude skill**
   - **Always orchestrate via the individual step skills**, so that each step can apply its own SKILL-change detection and `run.py` regeneration rules:
     - First call `/0-load-data` (and thus ensure `.claude/skills/0-load-data/run.py` is up to date)
     - Then, for each customer ID, invoke `/1-analyze`, `/2-guardrail`, `/3-offer`, `/4-content`, `/5-legal`, `/6-brand` in the order described above
   - Do **not** bypass the step SKILLs by calling their `run.py` files directly inside this skill; rely on their SKILL.md instructions to:
     - Compare `SKILL.md` vs `SKILL-backup.md`
     - Regenerate `.claude/skills/<step>/run.py` when the body changes
     - Refresh `SKILL-backup.md` after regeneration.

2. **Optional CLI orchestration script**
   - A separate Python script `.claude/skills/8-pipeline/run.py` MAY exist for command-line usage (e.g., `python3.11 .claude/skills/8-pipeline/run.py $ARGUMENTS`).
   - This script is **not** required for Claude skill invocation and SHOULD NOT be used from within this SKILL; it is only a convenience for running the pipeline from a shell.

3. **Flush cached results at the end**
   - After all per-customer steps have completed (for a single customer or for `all`), invoke `/9-flush-output $ARGUMENTS` to append the cached rows from `output_cache.json` into the `output` worksheet.

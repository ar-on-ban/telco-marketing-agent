---
name: 2-guardrail
description: Check if customer contact should be blocked by guardrails
---

## Input
- Customer ID: $ARGUMENTS
- Configuration data from `data_cache.json`

## Task
Check blocking conditions against customer data:

If customer has trigger:

1. **BLOCK if `active_billing_dispute` = TRUE**

2. **BLOCK if `days_since_last_contact` < 7**

A trigger can exist but contact can still be blocked by guardrails.

If customer has no trigger:
- Leave guardrail_notes and guardrail_approved empty

## Output
Write the following fields to `output_cache.json` under the customer's ID
- `guardrail_notes`: Explanation
- `guardrail_approved`: TRUE / FALSE

## Execution details

Work relative to the project root where `CLAUDE.md` lives and manage a persistent script in `.claude/skills/2-guardrail/run.py`:

1. **Skill-change detection** (do this FIRST)
   - Compare the **entire `SKILL.md` file content** (including YAML frontmatter and body) between:
     - `.claude/skills/2-guardrail/SKILL.md`
     - `.claude/skills/2-guardrail/SKILL-backup.md` (if it exists)
   - If `SKILL-backup.md` is missing or the files differ even by a single character -> go to step 2
   - Only if they match every character and `run.py` exists -> go to step 3

2. **Script generation** (when SKILL.md changed or run.py missing)
   - Generate a new `run.py` file in `.claude/skills/2-guardrail/` that:
     - Reads configuration and customer data from `data_cache.json` and `output_cache.json`
     - Implements the guardrail checks exactly as described in **Task**
     - Updates the `guardrail_notes` and `guardrail_approved` columns for the appropriate output row.
   - After generating, overwrite `SKILL-backup.md` with the current `SKILL.md`
   - Then run: `python3.11 .claude/skills/2-guardrail/run.py $ARGUMENTS`

3. **Run existing script** (when SKILL.md unchanged)
   - `python3.11 .claude/skills/2-guardrail/run.py $ARGUMENTS`

4. **CLI contract**
   - `run.py` must accept a single positional argument:
     - `$ARGUMENTS` is either a concrete customer ID like `C006` or the special keyword `all`
   - For `all`, the script should iterate all customers and apply the same guardrail logic, updating output rows accordingly.

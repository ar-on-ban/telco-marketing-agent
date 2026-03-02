---
name: 1-analyze
description: Analyze a customer to detect marketing triggers and infer intent
---

## Input
- Customer ID: $ARGUMENTS
- Configuration data from `data_cache.json`

## Tasks

1. **Load context from `data_cache.json`:**
   - `business_directive` — strategic guidelines
   - `workflow_examples` — few-shot examples for reasoning
   - `all_customers` — for relative comparison metrics

2. **Build a prompt to be sent to Claude API (Anthropic Python SDK). The prompt should include:**
   - Goal: to analyze all user data to detect if there's a meaningful trigger to contact them now.
   - Data: the customer's full record and aggregate statistics of all customers for comparison
   - Guide: to use the workflow examples (except the first "Example" row). Use these examples to understand the expected reasoning depth and approach. Apply similar thinking patterns to the current customer's unique situation.
   - Clear instructions to output: has_trigger, trigger_reason, customer_intent

3. **Call Claude API** with model `claude-sonnet-4-20250514`

4. **Parse the response** and write the following fields to `output_cache.json` under the customer's ID
- `customer_id`
- `timestamp`
- `has_trigger`: TRUE / FALSE
- `trigger_reason`: Explanation of the trigger or lack thereof. Use newlines (`\n`) to separate distinct points for readability within the cell.
- `customer_intent`: Explanation of intent inferred from the data. Use newlines (`\n`) to separate distinct points for readability within the cell.

## Execution details

Work relative to the project root where `CLAUDE.md` lives and manage a persistent script in `.claude/skills/1-analyze/run.py`:

1. **Skill-change detection**
   - Compare the **entire `SKILL.md` file content** (including YAML frontmatter and body) between:
     - `.claude/skills/1-analyze/SKILL.md`
     - `.claude/skills/1-analyze/SKILL-backup.md` (if it exists)
   - If `SKILL-backup.md` is missing or the files differ even by a single character -> go to step 2
   - Only if they match every character and `run.py` exists -> go to step 3

2. **Script generation** (when SKILL.md changed or run.py missing)
   - Generate a new `run.py` file in `.claude/skills/1-analyze/` that:
     - Reads the configuration from `data_cache.json`
     - Reads the input Google Sheets data as needed (customer record, prior outputs)
     - Implements the analysis tasks and writes the results to `output_cache.json` as described above.
   - After generating, overwrite `SKILL-backup.md` with the current `SKILL.md`
   - Then run: `python3.11 .claude/skills/1-analyze/run.py $ARGUMENTS`

3. **Run existing script** (when SKILL.md unchanged)
   - `python3.11 .claude/skills/1-analyze/run.py $ARGUMENTS`

4. **CLI contract**
   - `run.py` must accept a single positional argument:
     - `$ARGUMENTS` is either a concrete customer ID like `C006` or the special keyword `all`
   - For `all`, the script should iterate all customers and apply the same analysis logic, creating one output row per customer.

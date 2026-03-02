---
name: 6-brand
description: Brand compliance sub-agent using good/bad example comparison
---

## Input
- Customer ID: $ARGUMENTS
- Proposed content from `output_cache.json`
- Configuration data from `data_cache.json`

## Task
You are a **Brand Compliance Sub-Agent**.

If the customer has offer:

1. **Compare generated content**
   - Compare content against good/bad examples
   - Good examples: Content that follows brand guidelines (what to emulate)
   - Bad examples: Content that violates brand guidelines (what to avoid)
   - Does the content align more with good examples or bad examples?
   - Check tone, style, structure, language quality

2. **Make approval decision**
   - APPROVE if content reflects qualities of good examples
   - REJECT if content resembles bad examples
   - Provide specific feedback referencing which examples influenced the decision

If customer has no offer
   - Leave the brand_notes and brand_approved columns empty

## Output
Write the following fields to `output_cache.json` under the customer's ID
- `brand_notes`: Explanation referencing good/bad examples. Use newlines (`\n`) to separate distinct observations for readability within the cell.
- `brand_approved`: TRUE or FALSE

## Execution details

Work relative to the project root where `CLAUDE.md` lives and manage a persistent script in `.claude/skills/6-brand/run.py`:

1. **Skill-change detection** (do this FIRST)
   - Compare the **entire `SKILL.md` file content** (including YAML frontmatter and body) between:
     - `.claude/skills/6-brand/SKILL.md`
     - `.claude/skills/6-brand/SKILL-backup.md` (if it exists)
   - If `SKILL-backup.md` is missing or the files differ even by a single character -> go to step 2
   - Only if they match every character and `run.py` exists -> go to step 3

2. **Script generation** (when SKILL.md changed or run.py missing)
   - Generate a new `run.py` file in `.claude/skills/6-brand/` that:
     - Reads brand examples from `data_cache.json`
     - Reads the proposed content from `output_cache.json`
     - Compares it against good/bad examples and writes `brand_notes` and `brand_approved` appropriately.
   - After generating, overwrite `SKILL-backup.md` with the current `SKILL.md`
   - Then run: `python3.11 .claude/skills/6-brand/run.py $ARGUMENTS`

3. **Run existing script** (when SKILL.md unchanged)
   - `python3.11 .claude/skills/6-brand/run.py $ARGUMENTS`

4. **CLI contract**
   - `run.py` must accept a single positional argument:
     - `$ARGUMENTS` is either a concrete customer ID like `C006` or the special keyword `all`
   - For `all`, the script should iterate all customers and apply the brand compliance logic, updating output rows accordingly.

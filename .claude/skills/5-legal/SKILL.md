---
name: 5-legal
description: Legal compliance sub-agent to verify consent and regulatory requirements
---

## Input
- Customer ID: $ARGUMENTS
- Configuration data from `data_cache.json`
- Proposed content from `output_cache.json`

## Task
You are a **Legal Compliance Sub-Agent**.

If the customer has offer:

1. **Load legal checks from `data_cache.json`**
   - For each check, if the `rule` field contains a URL (starts with http:// or https://):
     - Fetch the content from that URL
     - Use the fetched content as the compliance rule
   - If the `rule` field is plain text, use it directly

2. **Review customer and content**
   - Apply legal checks to verify compliance
   - Use Claude API to evaluate the content against each rule

3. **Make approval decision**
   - APPROVE if all checks pass
   - REJECT if any legal concern exists

If customer has no offer
   - Leave the legal_notes and legal_approved columns empty

## Output
Write the following fields to `output_cache.json` under the customer's ID
- Column L `legal_notes`: Explanation of decision, listing any violations. Use newlines (`\n`) to separate each check result or violation for readability within the cell.
- Column M `legal_approved`: TRUE / FALSE

## Execution details

Work relative to the project root where `CLAUDE.md` lives and manage a persistent script in `.claude/skills/5-legal/run.py`:

1. **Skill-change detection** (do this FIRST)
   - Compare the **entire `SKILL.md` file content** (including YAML frontmatter and body) between:
     - `.claude/skills/5-legal/SKILL.md`
     - `.claude/skills/5-legal/SKILL-backup.md` (if it exists)
   - If `SKILL-backup.md` is missing or the files differ even by a single character -> go to step 2
   - Only if they match every character and `run.py` exists -> go to step 3

2. **Script generation** (when SKILL.md changed or run.py missing)
   - Generate a new `run.py` file in `.claude/skills/5-legal/` that:
     - Reads configuration (legal checks) from `data_cache.json`
     - For each legal check, detects if the `rule` field contains a URL and fetches the content
     - Reads the proposed content from `output_cache.json`
     - Uses Claude API to evaluate content against legal rules (original or URL-fetched)
     - Writes `legal_notes` and `legal_approved` into the correct columns
   - After generating, overwrite `SKILL-backup.md` with the current `SKILL.md`
   - Then run: `python3.11 .claude/skills/5-legal/run.py $ARGUMENTS`

3. **Run existing script** (when SKILL.md unchanged)
   - `python3.11 .claude/skills/5-legal/run.py $ARGUMENTS`

4. **CLI contract**
   - `run.py` must accept a single positional argument:
     - `$ARGUMENTS` is either a concrete customer ID like `C006` or the special keyword `all`
   - For `all`, the script should iterate all customers and apply the legal compliance logic, updating output rows accordingly.

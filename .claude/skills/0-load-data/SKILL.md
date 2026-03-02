---
name: 0-load-data
description: Load all configuration data from Google Sheets into json
---

## Purpose

To load ALL configuration data from Google Sheets into a json serving as cache.

## Task

1. Make sure to load all configuration data from Google Sheets:

1. **Customer records** (from "customer_data" worksheet)
2. **Workflow examples** (from "input" worksheet, skip "Example" row)
3. **Legal checks** (from "input" worksheet LEGAL AGENT section)
4. **Brand examples** (from "input" worksheet BRAND AGENT section)
5. **Business directive** (from "input" worksheet)
6. **Content tone** (from "input" worksheet)

2. Write `data_cache.json` file containing:
- `all_customers`: List of all customer records
- `business_directive`: Business directive text
- `content_tone`: Content writing tone guidelines
- `workflow_examples`: Few-shot workflow examples (Team 1-5 rows)
- `legal_checks`: Legal compliance checks
- `brand_examples`: Brand compliance good/bad examples

## Parsing Strategy (input worksheet)

Use **marker-based, header-driven parsing** — do not hard-code column letters or row numbers.

**Critical rule:** Section markers (WORKFLOW EXAMPLES, LEGAL AGENT, BRAND AGENT, BUSINESS DIRECTIVE, CONTENT TONE) can appear in **any cell** of a row, not just column A. Column A is typically used for row labels like "Team 1", "Example", "Check 1", while section markers are usually in column B. Always scan all cells in a row when looking for markers.

**Critical rule:** When iterating rows within a section, always check for the next section marker **before** skipping empty rows. Section marker rows often have an empty column A (e.g., column A is blank but column B contains "LEGAL AGENT"). If you skip rows with empty column A first, you'll miss section boundaries and bleed data between sections.

**General approach:**
1. Scan all rows to find section markers by checking every cell in each row
2. Within each section, discover the column structure from header rows
3. Parse data rows relative to section boundaries using discovered headers
4. Sections can appear in any order in the worksheet

**BUSINESS DIRECTIVE & CONTENT TONE:**
- Find row containing "BUSINESS DIRECTIVE" in any cell (use substring match, case-insensitive)
- Extract the value from the next non-empty cell in that same row (the cell after the marker)
- Same approach for "CONTENT TONE" (also matches "CONTENT WRITING TONE")

**WORKFLOW EXAMPLES section:**
- Find row containing "WORKFLOW EXAMPLES" marker (any cell)
- Next row contains column headers — map these to discover column positions
- For each subsequent row, **first** check if any cell contains a different section marker (LEGAL AGENT, BRAND AGENT, BUSINESS DIRECTIVE, CONTENT TONE) — if so, stop
- Skip any row containing "Example" in the first cell
- Skip rows where the first cell is empty
- Parse rows where the first cell starts with "Team" (Team 1, Team 2, etc.)
- For each Team row, extract values using the discovered column header mapping
- Expected fields: customer_signals, trigger_detection, intent_inference, offer_decision, generated_content_sample

**LEGAL AGENT section:**
- Find row containing "LEGAL AGENT" marker (any cell)
- For each subsequent row, **first** check if any cell contains a different section marker — if so, stop
- Skip Purpose/description rows
- Parse rows where any cell starts with "Check" (Check 1, Check 2, etc.)
- For each check row, extract: check name and its rule/description from the adjacent cell
- Only include checks that have a non-empty rule

**BRAND AGENT section:**
- Find row containing "BRAND AGENT" marker (any cell)
- Skip Purpose/description rows
- Find header row containing "Good example" / "Bad example" to discover column positions
- Parse Team rows below (Team 1, Team 2, etc.) until another section marker or end of data
- For each Team row, extract: team name, good example, bad example using discovered positions

## Execution details

1. First, work relative to the project root where `CLAUDE.md` lives.

2. **Skill-change detection** (do this FIRST)
   - Compare the **entire `SKILL.md` file content** (including YAML frontmatter and body) between:
     - `.claude/skills/0-load-data/SKILL.md`
     - `.claude/skills/0-load-data/SKILL-backup.md` (if it exists)
   - If `SKILL-backup.md` is missing or the files differ even by a single character -> go to step 3
   - Only if they match every character and `run.py` exists -> go to step 4

3. **Script generation** (when SKILL.md changed or run.py missing)
   - Generate a new `run.py` file at `.claude/skills/0-load-data/run.py` that:
     - Uses `python3.11`
     - Authenticates to Google Sheets via `service_account.json` and the `GOOGLE_SHEET_URL` from `.env`
     - Loads all configuration data exactly as described in **What This Skill Loads**
     - Writes the aggregated configuration into `data_cache.json` in the project root (UTF-8, pretty-printed JSON)
     - Prints a concise console summary (counts and short previews)
   - After generating, overwrite `SKILL-backup.md` with the current `SKILL.md`
   - Then run: `python3.11 .claude/skills/0-load-data/run.py`

4. **Run existing script** (when SKILL.md unchanged)
   - `python3.11 .claude/skills/0-load-data/run.py`

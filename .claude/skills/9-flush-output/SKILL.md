---
name: 9-flush-output
description: Flush cached customer results from output_cache.json into the Google Sheets output worksheet
---

## Input
- Customer selector: $ARGUMENTS
  - Single customer ID (e.g., `C001`) -> flush that customer's cached row
  - `all` -> flush all customers currently present in `output_cache.json`

## Task

This skill is responsible for the **only** writes to the Google Sheet `output` worksheet.
All other skills (1-6, and optionally 7) must read/write only local cache files
(`data_cache.json` and `output_cache.json`).

1. **Load caches**
   - Read `data_cache.json` (for context if needed).
   - Read `output_cache.json` from the project root.
   - If `output_cache.json` is missing or contains no `customers`, print a clear message and exit.

2. **Connect to Google Sheets**
   - Use the same authentication pattern as `/0-load-data` (via `.env` and `service_account.json`).
   - Open the `output` worksheet.

3. **Ensure header row exists**
   - If the worksheet is empty, write the standard header row:
     - `customer_id`, `timestamp`, `has_trigger`, `trigger_reason`, `customer_intent`,
       `guardrail_notes`, `guardrail_approved`, `offer_decision`, `channel`,
       `content_title`, `content_body`, `legal_notes`, `legal_approved`,
       `brand_notes`, `brand_approved`.

4. **Determine which customers to flush**
   - If `$ARGUMENTS` is `all`, flush all keys under `output_cache.json["customers"]`.
   - If `$ARGUMENTS` is a specific customer ID, flush only that entry.
   - For each selected customer:
     - Skip if the record is missing in `customers`.
     - Skip if the record has already been flushed (e.g. internal `_flushed` flag is `TRUE`).

5. **Append-only write semantics**
   - Determine the current last non-empty row in `output`.
   - For each customer to flush, build a row in the exact header order above, using empty strings for any missing fields.
   - **Append** one new row per customer at the bottom of the sheet; do not overwrite existing rows.
   - Use batched writes if available (e.g., `append_rows`) to minimize API calls, but correctness is more important than optimization.

6. **Mark flushed entries**
   - After a successful append for a customer:
     - Mark that customer's record in `output_cache.json["customers"]` with an internal flag such as `_flushed: true` and optionally store a `flushed_at` timestamp.
   - Save `output_cache.json` back to disk.

7. **Reporting**
   - Print how many customers were flushed and how many were skipped (missing / already flushed).

## Usage notes

- This skill is intended to be:
  - **Automatically invoked** by `/8-pipeline` at the end of a full workflow (with the same argument: single ID or `all`).
  - **Automatically invoked** by the last step in a one-off mini workflow (e.g. `/3-offer`, `/4-content`, or `/6-brand`) for that specific customer ID.
  - Manually invokable by the user when needed.

## Execution details

Work relative to the project root where `CLAUDE.md` lives and manage a persistent script in `.claude/skills/9-flush-output/run.py`:

1. **Skill-change detection** (do this FIRST)
   - Compare the **entire `SKILL.md` file content** (including YAML frontmatter and body) between:
     - `.claude/skills/9-flush-output/SKILL.md`
     - `.claude/skills/9-flush-output/SKILL-backup.md` (if it exists)
   - If `SKILL-backup.md` is missing or the files differ even by a single character -> go to step 2
   - Only if they match every character and `run.py` exists -> go to step 3

2. **Script generation** (when SKILL.md changed or run.py missing)
   - Generate a new `run.py` that:
     - Reads from `output_cache.json`
     - Connects to Google Sheets via `service_account.json` and `.env`
     - Appends cached results to the `output` worksheet
     - Removes flushed entries from the cache
   - After generating, overwrite `SKILL-backup.md` with the current `SKILL.md`
   - Then run: `python3.11 .claude/skills/9-flush-output/run.py $ARGUMENTS`

3. **Run existing script** (when SKILL.md unchanged)
   - `python3.11 .claude/skills/9-flush-output/run.py $ARGUMENTS`

4. **CLI contract**
   - `run.py` must accept a single positional argument:
     - `$ARGUMENTS` is either a concrete customer ID like `C006` or the special keyword `all`

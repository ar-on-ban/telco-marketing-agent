---
name: 4-content
description: Generate marketing content for the customer
---

## Input
- Customer ID: $ARGUMENTS
- Customer analysis and offer from `output_cache.json`
- Configuration data from `data_cache.json`

## Tasks

1. **Load context from `data_cache.json`:**
   - `business_directive` — strategic guidelines
   - `content_tone` — writing style and tone guidelines
   - `workflow_examples` — for understanding expected content quality

2. **Load from `output_cache.json`:**
   - The customer's offer_decision and preferred_channel from prior steps

3. **Build a prompt to be sent to Claude API (Anthropic Python SDK). The prompt should include:**
   - Goal: generate marketing content matching the customer's preferred channel format
   - Data: business directive, content tone, customer data + offer decision
   - Channel format requirements (include verbatim in prompt):
     - `app`: push notification format with less than 100 characters, use a few emojis
     - `email`: email subject and body with minimum 350 characters
     - `call`: phone script for agent with minimum 500 characters
     - `text`: whatsapp, messenger, or sms with less than 200 characters
   - Guide: use the workflow examples (except the first "Example" row). Use the generated_content_sample field to understand the expected tone and structure. Create original content that reflects this quality level for the current customer's unique situation.
   - Clear instructions to output JSON: {"channel": "...", "title": "...", "body": "..."}

4. **Call Claude API** with model `claude-sonnet-4-20250514`

5. **Parse the JSON response** and write the following fields to `output_cache.json` under the customer's ID:
   - `channel`: app, email, call, text, or empty
   - `content_title`: Title or empty
   - `content_body`: Message or empty

## Execution details

Work relative to the project root where `CLAUDE.md` lives and manage a persistent script in `.claude/skills/4-content/run.py`:

1. **Skill-change detection** (do this FIRST)
   - Compare the **entire `SKILL.md` file content** (including YAML frontmatter and body) between:
     - `.claude/skills/4-content/SKILL.md`
     - `.claude/skills/4-content/SKILL-backup.md` (if it exists)
   - If `SKILL-backup.md` is missing or the files differ even by a single character -> go to step 2
   - Only if they match every character and `run.py` exists -> go to step 3

2. **Script generation** (when SKILL.md changed or run.py missing)
   - Generate a new `run.py` file in `.claude/skills/4-content/` that:
     - Reads configuration and prior step outputs from `data_cache.json` and `output_cache.json`
     - Chooses the appropriate channel and generates content following the tone and workflow examples
     - Writes `channel`, `content_title`, and `content_body` to `output_cache.json` as specified above.
   - After generating, overwrite `SKILL-backup.md` with the current `SKILL.md`
   - Then run: `python3.11 .claude/skills/4-content/run.py $ARGUMENTS`

3. **Run existing script** (when SKILL.md unchanged)
   - `python3.11 .claude/skills/4-content/run.py $ARGUMENTS`

4. **CLI contract**
   - `run.py` must accept a single positional argument:
     - `$ARGUMENTS` is either a concrete customer ID like `C006` or the special keyword `all`
   - For `all`, the script should iterate all customers and apply the content generation logic, updating output rows accordingly.

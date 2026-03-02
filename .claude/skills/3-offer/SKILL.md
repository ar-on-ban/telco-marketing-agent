---
name: 3-offer
description: Recommend an appropriate product offer based on trigger and intent
---

## Input
- Customer ID: $ARGUMENTS
- Customer analysis from `output_cache.json`
- Configuration data from `data_cache.json`

## Tasks

1. **Load context from `data_cache.json`:**
   - `business_directive` — strategic guidelines for offer selection
   - `workflow_examples` — few-shot examples showing trigger->offer reasoning

2. **Load from `output_cache.json`:**
   - The customer's trigger_reason, customer_intent, and guardrail_approved from prior steps

3. **Build a prompt to be sent to Claude API (Anthropic Python SDK). The prompt should include:**
   - Goal: recommend an appropriate offer if guardrail_approved=TRUE, otherwise leave empty
   - Data: business directive, customer data + analysis results
   - Product catalog (include verbatim in prompt):
     - Mobile: Prepaid Basic, Prepaid Plus, Postpaid S/M/L, Family Plan
     - Internet: Home Internet Basic, Home Internet 500, Home Internet 1000
     - Add-ons: Extra data pack, EU roaming pack, Device insurance, Streaming bundle, Cloud storage
   - Guide: use the workflow examples (except the first "Example" row). Use these examples to understand how triggers and intents inform product recommendations. Apply similar reasoning to find the best fit for this customer's specific needs.
   - Clear instructions to output: offer_decision

4. **Call Claude API** with model `claude-sonnet-4-20250514`

5. **Parse the response** and write the following fields to `output_cache.json` under the customer's ID:
   - `offer_decision`: The recommended product/offer (or empty if no trigger/guardrail blocked)

## Execution details

Work relative to the project root where `CLAUDE.md` lives and manage a persistent script in `.claude/skills/3-offer/run.py`:

1. **Skill-change detection** (do this FIRST)
   - Compare the **entire `SKILL.md` file content** (including YAML frontmatter and body) between:
     - `.claude/skills/3-offer/SKILL.md`
     - `.claude/skills/3-offer/SKILL-backup.md` (if it exists)
   - If `SKILL-backup.md` is missing or the files differ even by a single character -> go to step 2
   - Only if they match every character and `run.py` exists -> go to step 3

2. **Script generation** (when SKILL.md changed or run.py missing)
   - Generate a new `run.py` file in `.claude/skills/3-offer/` that:
     - Reads configuration and customer analysis data from `data_cache.json` and `output_cache.json`
     - Applies the product catalog and business directive logic described in **Task**
     - Updates the `offer_decision` column for the appropriate output row.
   - After generating, overwrite `SKILL-backup.md` with the current `SKILL.md`
   - Then run: `python3.11 .claude/skills/3-offer/run.py $ARGUMENTS`

3. **Run existing script** (when SKILL.md unchanged)
   - `python3.11 .claude/skills/3-offer/run.py $ARGUMENTS`

4. **CLI contract**
   - `run.py` must accept a single positional argument:
     - `$ARGUMENTS` is either a concrete customer ID like `C006` or the special keyword `all`
   - For `all`, the script should iterate all customers and apply the offer logic, updating output rows accordingly.

# Agentic Marketing Workshop

A skills-based agentic AI pipeline that analyzes telecom customers and generates personalized marketing content — built with Claude Code as the orchestration layer.

**This is an educational project**, originally designed as a hands-on workshop for C-level executives at a European telco. It is not intended for production use. The goal is to teach non-technical stakeholders about shaping and controlling agentic AI behavior through a simplified collaborative Google Sheet interface — editing few-shot examples, tuning business directives, and adjusting compliance rules — all without touching code.

## Architecture

```
Google Sheet (control plane)          Claude Code (execution engine)
┌─────────────────────────┐          ┌─────────────────────────────┐
│ customer_data worksheet │──load──▶│ /0-load-data                │
│ input worksheet         │          │   ├─ business directive      │
│   ├─ business directive │          │   ├─ content tone            │
│   ├─ content tone       │          │   ├─ workflow examples       │
│   ├─ workflow examples  │          │   ├─ legal checks            │
│   └─ brand examples     │          │   └─ brand examples          │
└─────────────────────────┘          │                               │
                                     │ Per-customer pipeline:        │
┌─────────────────────────┐          │   /1-analyze    → trigger?    │
│ output worksheet        │◀─flush──│   /2-guardrail  → blocked?    │
│   (append-only results) │          │   /3-offer      → which plan? │
└─────────────────────────┘          │   /4-content    → message     │
                                     │   /5-legal      → compliant?  │
                                     │   /6-brand      → on-brand?   │
                                     └─────────────────────────────┘
```

## How the Skills Work

Each skill is defined by a `SKILL.md` file containing written instructions for what the skill should do. When a skill is invoked, Claude Code reads the instructions and generates a Python script (`run.py`) that implements them. To demonstrate live editability — and to allow skill logic to be changed on the fly — every skill includes a change-detection mechanism: if the `SKILL.md` has been modified since the last run, the `run.py` is automatically regenerated. This means that during the workshop one can rewrite a skill's behavior in plain English and see the effect on the next execution.

The skills represent simplified steps an agentic marketing pipeline might take:

1. **Analyze** (`/1-analyze`) — Examine customer data to identify meaningful triggers and infer intent. Should we contact this customer now, and why?
2. **Guardrail** (`/2-guardrail`) — Apply deterministic blocking rules (e.g., active billing dispute, contacted too recently). Hard gates that override any AI recommendation.
3. **Offer** (`/3-offer`) — Based on the detected intent, select an appropriate product offer from the catalog.
4. **Content** (`/4-content`) — Generate a marketing message tailored to the customer's preferred channel (app push, email, phone script, or text).
5. **Legal** (`/5-legal`) — Review the generated content against configurable compliance rules.
6. **Brand** (`/6-brand`) — Compare the content against good/bad examples to ensure brand consistency.

The **pipeline** skill (`/8-pipeline`) simply executes all of the above in sequence for one or all customers. The **flush-output** skill (`/9-flush-output`) writes all cached results back to Google Sheets in a single batch — this is faster than writing after each individual skill execution.

## Workshop Flow

The workshop is structured around iterative pipeline runs that reveal how input data shapes agent behavior:

1. **First run — no input data.** Start with the `input` worksheet empty (or nearly empty). Run the pipeline and observe what the agent does with customer data alone, without few-shot examples, business directives, or compliance rules. The results are usually generic and unguided.

2. **Add input data step by step.** After each addition, re-run the pipeline and compare the results:
   - Add a **business directive** → watch the agent shift its priorities
   - Add **workflow examples** (few-shot) → watch reasoning quality and consistency improve
   - Add **legal checks** → watch content get flagged or approved
   - Add **brand examples** (good/bad pairs) → watch the tone and style change
   - Adjust **content tone** → watch the messaging adapt

3. **Observe the difference.** Through this step-by-step process, participants get hands-on experience shaping agent behavior — in a controlled environment with complete data and without the complexity of real-time data streaming.

## Skills Reference

| Skill | Purpose | AI-powered? |
|-------|---------|-------------|
| `/0-load-data` | Load all config from Google Sheets into local cache | No |
| `/1-analyze` | Detect marketing triggers and infer customer intent | Yes (Claude API) |
| `/2-guardrail` | Check blocking conditions (billing disputes, recent contact) | No (rule-based) |
| `/3-offer` | Recommend a product from the catalog | Yes (Claude API) |
| `/4-content` | Generate channel-appropriate marketing content | Yes (Claude API) |
| `/5-legal` | Legal compliance review against configurable rules (supports live URLs as rules — e.g., link to a policy page) | Yes (Claude API) |
| `/6-brand` | Brand compliance via good/bad example comparison | Yes (Claude API) |
| `/8-pipeline` | Run full pipeline for one or all customers | Orchestrator |
| `/9-flush-output` | Append cached results to Google Sheet | No |

## Setup

### Prerequisites
- Python 3.11+
- A Google Cloud service account with Sheets API access
- An Anthropic API key
- Claude Code CLI (for skill invocation) or use `orchestrator.py` for standalone execution

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd telco-marketing-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Google Sheets setup

1. Make a copy of the [workshop template sheet](https://docs.google.com/spreadsheets/d/1JI7ScsppIb7vjr_7PFSZicgKpu9si-AkZyyDPf5JuvA/edit?usp=sharing) (File → Make a copy)
2. The sheet contains three worksheets:
   - **`customer_data`** — synthetic telecom customer records
   - **`input`** — configuration data (business directive, workflow examples, legal checks, brand examples)
   - **`output`** — left empty, the pipeline writes results here
3. To simulate the workshop flow, clear content from the `input` worksheet and add it back step by step as you run the pipeline

### 3. Google service account

1. In Google Cloud Console, create a service account and download the JSON key
2. Save it as `service_account.json` in the project root
3. Share your Google Sheet copy with the service account email (Editor access)

### 4. Environment variables

```bash
cp .env.example .env
# Edit .env with your Google Sheet URL and Anthropic API key
```

### 5. Run

Each skill can be run individually for a single customer or for all customers. During the workshop, we typically use the pipeline skill with a specific customer ID as argument — or run it for all customers (which takes longer).

**Via Claude Code (interactive):**
```bash
claude
# Then use slash commands:
# /8-pipeline C005        — run full pipeline for one customer
# /8-pipeline all         — run full pipeline for all customers
# /1-analyze C005         — run just the analysis step
```

**Via orchestrator (standalone):**
```bash
source venv/bin/activate  # if not already active
python3 orchestrator.py 8-pipeline C005
python3 orchestrator.py 8-pipeline all
python3 orchestrator.py 1-analyze C005
```

## Workshop Format

The workshop is designed for 10-15 participants, broken into teams of 3-4. Each team gets their own row in the `input` worksheet (Team 1, Team 2, etc.) to collaboratively fill in workflow examples, brand examples, and other configuration data. This way, every team contributes their perspective on how the agent should behave — and the pipeline incorporates all of their inputs on the next run.

## Design Decisions

**Why Google Sheets?** The collaborative, real-time editing nature is the point. Workshop participants edit the Sheet live and immediately see how it changes pipeline behavior — making AI control tangible for non-technical stakeholders.

**Why Claude Code skills?** Each pipeline step is a self-contained skill with its own `SKILL.md` (instructions) and `run.py` (implementation). The skill system provides auto-regeneration: if you edit a `SKILL.md`, the next invocation detects the change and regenerates the corresponding `run.py`. This makes the agent's logic transparent and editable in plain English.

**Why are the `run.py` files included?** The Python scripts in each skill folder were auto-generated by Claude Code from the `SKILL.md` instructions. They are included in the repo so that the full pipeline logic is visible without needing to run anything. In a live workshop, these scripts would be regenerated on the fly whenever a `SKILL.md` is edited — but for browsing purposes, having them checked in makes it easier to see what the agent actually does at each step.

**Why local caches?** The pipeline uses `data_cache.json` (input) and `output_cache.json` (intermediate results) to minimize Google Sheets API calls and enable step-by-step debugging. Only `/9-flush-output` writes to the Sheet.

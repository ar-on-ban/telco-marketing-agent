# Marketing Agent

Skills-based marketing automation agent that analyzes telecom customers and generates personalized marketing content.

## Environment

- Google Sheet connected via `service_account.json`
- Sheet URL configured in `.env` as `GOOGLE_SHEET_URL`
- Use `gspread` library with `google.oauth2.service_account.Credentials`
- Use `python3.11` for all scripts

## Skills

Skill          | Purpose |
`/0-load-data` | Load configuration data and bootstrap caches
`/1-analyze`   | Detect trigger, infer customer intent (writes to `output_cache.json` only)
`/2-guardrail` | Check blocking conditions (writes to `output_cache.json` only)
`/3-offer`     | Recommend appropriate product (writes to `output_cache.json` only)
`/4-content`   | Generate marketing content (writes to `output_cache.json` only)
`/5-legal`     | Legal compliance check (writes to `output_cache.json` only)
`/6-brand`     | Brand compliance check (writes to `output_cache.json` only)
`/7-visualize` | Generate HTML email preview from cached content
`/8-pipeline`  | Run full pipeline for customer(s) using cached writes
`/9-flush-output` | Append cached results from `output_cache.json` to the Google Sheet `output` worksheet

#!/usr/bin/env python3.11
"""Flush cached customer results from output_cache.json into the Google Sheet.

This script appends new rows to the `output` worksheet for customers whose
records are present in `output_cache.json["customers"]` and not yet flushed.
It never overwrites existing rows.
"""

import json
import os
import sys
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
SA_PATH = os.path.join(PROJECT_ROOT, "service_account.json")
OUTPUT_CACHE_PATH = os.path.join(PROJECT_ROOT, "output_cache.json")

OUTPUT_HEADERS = [
    "customer_id",
    "timestamp",
    "has_trigger",
    "trigger_reason",
    "customer_intent",
    "guardrail_notes",
    "guardrail_approved",
    "offer_decision",
    "channel",
    "content_title",
    "content_body",
    "legal_notes",
    "legal_approved",
    "brand_notes",
    "brand_approved",
]


def load_env(path: str) -> dict[str, str]:
    env: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def authenticate() -> gspread.Spreadsheet:
    env = load_env(ENV_PATH)
    sheet_url = env.get("GOOGLE_SHEET_URL")
    if not sheet_url:
        print("ERROR: GOOGLE_SHEET_URL not found in .env")
        sys.exit(1)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(SA_PATH, scopes=scopes)
    gc = gspread.authorize(creds)
    return gc.open_by_url(sheet_url)


def load_output_cache() -> dict:
    if not os.path.exists(OUTPUT_CACHE_PATH):
        print("No output_cache.json found - nothing to flush.")
        sys.exit(0)
    with open(OUTPUT_CACHE_PATH, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"ERROR: Failed to parse output_cache.json: {exc}")
            sys.exit(1)

    # Initialize meta if not present
    if "meta" not in data or not isinstance(data["meta"], dict):
        data["meta"] = {}

    # Handle both nested "customers" structure and direct customer IDs at root
    # If "customers" is empty, populate it from root-level customer IDs
    if "customers" not in data or not data.get("customers"):
        # Create customers dict from root-level customer IDs
        customers = {}
        for key, value in data.items():
            if key.startswith("C") and isinstance(value, dict):
                customers[key] = value
        data["customers"] = customers

    if not isinstance(data["customers"], dict) or not data["customers"]:
        print("output_cache.json has no customer records - nothing to flush.")
        sys.exit(0)

    return data


def save_output_cache(cache: dict) -> None:
    with open(OUTPUT_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def ensure_header(ws: gspread.Worksheet) -> None:
    values = ws.get_all_values()
    if not values:
        ws.append_row(OUTPUT_HEADERS, value_input_option="USER_ENTERED")
        return
    header = values[0]
    if header != OUTPUT_HEADERS:
        # Keep existing header; we still rely on the defined OUTPUT_HEADERS order
        return


def main():
    if len(sys.argv) < 2:
        print("Usage: run.py <customer_id | all>")
        sys.exit(1)

    target = sys.argv[1].strip()
    cache = load_output_cache()
    customers: dict = cache.get("customers", {})

    if not customers:
        print("output_cache.json contains no customers - nothing to flush.")
        sys.exit(0)

    if target.lower() == "all":
        target_ids = list(customers.keys())
    else:
        if target not in customers:
            print(f"ERROR: Customer {target} not found in output_cache.json")
            sys.exit(1)
        target_ids = [target]

    print("Connecting to Google Sheets...")
    ss = authenticate()
    ws = ss.worksheet("output")

    ensure_header(ws)
    existing = ws.get_all_values()
    data_row_count = max(len(existing) - 1, 0)
    next_row_index = data_row_count + 2  # header + existing data

    rows_to_append: list[list[str]] = []
    flushed_ids: list[str] = []
    skipped_missing: list[str] = []

    for cid in target_ids:
        record = customers.get(cid)
        if not record:
            skipped_missing.append(cid)
            continue

        row = []
        for key in OUTPUT_HEADERS:
            row.append(str(record.get(key, "")))
        rows_to_append.append(row)
        flushed_ids.append(cid)

    if not rows_to_append:
        print("No customers to flush (all selected customers missing).")
        sys.exit(0)

    # Append rows in a single batch if possible
    ws.append_rows(rows_to_append, value_input_option="USER_ENTERED")

    # Remove flushed customers from both the nested structure and root level
    for cid in flushed_ids:
        customers.pop(cid, None)
        # Also remove from root level if it exists there
        cache.pop(cid, None)

    cache["customers"] = customers
    save_output_cache(cache)

    print(f"Flushed {len(flushed_ids)} customer(s) to Google Sheets starting at row {next_row_index}.")
    if skipped_missing:
        print(f"Skipped {len(skipped_missing)} missing customer(s): {', '.join(skipped_missing)}")


if __name__ == "__main__":
    main()

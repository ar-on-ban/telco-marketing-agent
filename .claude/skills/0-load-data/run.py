#!/usr/bin/env python3.11
"""
Load all configuration data from Google Sheets into data_cache.json
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# Load environment variables
load_dotenv()

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SERVICE_ACCOUNT_PATH = PROJECT_ROOT / "service_account.json"
OUTPUT_FILE = PROJECT_ROOT / "data_cache.json"
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL")

# Authenticate to Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file(str(SERVICE_ACCOUNT_PATH), scopes=SCOPES)
client = gspread.authorize(creds)

# Open the spreadsheet
spreadsheet = client.open_by_url(GOOGLE_SHEET_URL)

print("Loading configuration data from Google Sheets...")

# 1. Load customer data from "customer_data" worksheet
customer_ws = spreadsheet.worksheet("customer_data")
customer_rows = customer_ws.get_all_values()
customer_headers = customer_rows[0]
all_customers = []
for row in customer_rows[1:]:
    if row and row[0]:
        customer = {customer_headers[i]: row[i] for i in range(len(customer_headers)) if i < len(row)}
        all_customers.append(customer)

print(f"Loaded {len(all_customers)} customers")

# 2. Load data from "input" worksheet
input_ws = spreadsheet.worksheet("input")
all_rows = input_ws.get_all_values()

# Section markers to detect boundaries
SECTION_MARKERS = ["WORKFLOW EXAMPLES", "LEGAL AGENT", "BRAND AGENT", "BUSINESS DIRECTIVE", "CONTENT TONE", "CONTENT WRITING TONE"]

def row_contains_marker(row, exclude=None):
    """Check if any cell in a row contains a section marker. Returns the marker found or None."""
    for cell in row:
        cell_upper = str(cell).upper().strip()
        for marker in SECTION_MARKERS:
            if marker == exclude:
                continue
            if marker in cell_upper:
                return marker
    return None

def find_row_with_marker(rows, marker):
    """Find index of row containing marker in any cell (case-insensitive substring match)."""
    for idx, row in enumerate(rows):
        if any(marker.upper() in str(cell).upper() for cell in row):
            return idx
    return -1

# Initialize data structures
business_directive = ""
content_tone = ""
workflow_examples = []
legal_checks = []
brand_examples = []

# Parse BUSINESS DIRECTIVE
bd_idx = find_row_with_marker(all_rows, "BUSINESS DIRECTIVE")
if bd_idx >= 0:
    for cell in all_rows[bd_idx]:
        if cell and "BUSINESS DIRECTIVE" not in cell.upper():
            business_directive = cell
            break

# Parse CONTENT TONE (also matches "CONTENT WRITING TONE")
ct_idx = find_row_with_marker(all_rows, "CONTENT TONE")
if ct_idx < 0:
    ct_idx = find_row_with_marker(all_rows, "CONTENT WRITING TONE")
if ct_idx >= 0:
    for cell in all_rows[ct_idx]:
        cell_upper = cell.upper() if cell else ""
        if cell and "CONTENT TONE" not in cell_upper and "CONTENT WRITING TONE" not in cell_upper:
            content_tone = cell
            break

print(f"Loaded business directive ({len(business_directive)} chars)")
print(f"Loaded content tone ({len(content_tone)} chars)")

# Parse WORKFLOW EXAMPLES
wf_idx = find_row_with_marker(all_rows, "WORKFLOW EXAMPLES")
if wf_idx >= 0:
    header_row = all_rows[wf_idx + 1]
    col_map = {header.strip().lower().replace(" ", "_"): i for i, header in enumerate(header_row) if header.strip()}

    for row_idx in range(wf_idx + 2, len(all_rows)):
        row = all_rows[row_idx]

        # CRITICAL: Check for section markers BEFORE skipping empty rows
        if row_contains_marker(row, exclude="WORKFLOW EXAMPLES"):
            break

        if not row or not row[0]:
            continue

        if "Example" in row[0]:
            continue

        if row[0].startswith("Team"):
            example = {}
            for field in ["customer_signals", "trigger_detection", "intent_inference", "offer_decision", "generated_content_sample"]:
                if field in col_map:
                    example[field] = row[col_map[field]] if col_map[field] < len(row) else ""
            if example:
                workflow_examples.append(example)

print(f"Loaded {len(workflow_examples)} workflow examples")

# Parse LEGAL AGENT section
legal_idx = find_row_with_marker(all_rows, "LEGAL AGENT")
if legal_idx >= 0:
    for row_idx in range(legal_idx + 1, len(all_rows)):
        row = all_rows[row_idx]

        # CRITICAL: Check for section markers BEFORE skipping empty rows
        if row_contains_marker(row, exclude="LEGAL AGENT"):
            break

        if not row or not any(row):
            continue

        for cell_idx, cell in enumerate(row):
            if cell and cell.startswith("Check"):
                check_name = cell.strip()
                rule = row[cell_idx + 1] if cell_idx + 1 < len(row) else ""
                if rule:
                    legal_checks.append({
                        "check": check_name,
                        "rule": rule
                    })
                break

print(f"Loaded {len(legal_checks)} legal checks")

# Parse BRAND AGENT section
brand_idx = find_row_with_marker(all_rows, "BRAND AGENT")
if brand_idx >= 0:
    header_idx = -1
    for row_idx in range(brand_idx + 1, min(brand_idx + 10, len(all_rows))):
        row = all_rows[row_idx]
        if any("good example" in str(cell).lower() for cell in row):
            header_idx = row_idx
            break

    if header_idx >= 0:
        header_row = all_rows[header_idx]
        good_col = -1
        bad_col = -1
        for idx, cell in enumerate(header_row):
            if "good example" in cell.lower():
                good_col = idx
            elif "bad example" in cell.lower():
                bad_col = idx

        for row_idx in range(header_idx + 1, len(all_rows)):
            row = all_rows[row_idx]

            # CRITICAL: Check for section markers BEFORE skipping empty rows
            if row_contains_marker(row, exclude="BRAND AGENT"):
                break

            if not row or not row[0]:
                continue

            if row[0].startswith("Team"):
                example = {
                    "team": row[0],
                    "good_example": row[good_col] if good_col >= 0 and good_col < len(row) else "",
                    "bad_example": row[bad_col] if bad_col >= 0 and bad_col < len(row) else ""
                }
                brand_examples.append(example)

print(f"Loaded {len(brand_examples)} brand examples")

# Assemble the cache
data_cache = {
    "all_customers": all_customers,
    "business_directive": business_directive,
    "content_tone": content_tone,
    "workflow_examples": workflow_examples,
    "legal_checks": legal_checks,
    "brand_examples": brand_examples
}

# Write to data_cache.json
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data_cache, f, ensure_ascii=False, indent=2)

print(f"\nConfiguration data written to {OUTPUT_FILE}")
print(f"\nSummary:")
print(f"  - {len(all_customers)} customers")
print(f"  - {len(workflow_examples)} workflow examples")
print(f"  - {len(legal_checks)} legal checks")
print(f"  - {len(brand_examples)} brand examples")
print(f"  - Business directive: {len(business_directive)} chars")
print(f"  - Content tone: {len(content_tone)} chars")

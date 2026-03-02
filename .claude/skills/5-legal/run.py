#!/usr/bin/env python3.11
"""
Legal compliance sub-agent to verify consent and regulatory requirements
"""

import json
import os
import sys
import anthropic
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_data_cache():
    """Load configuration data from data_cache.json"""
    with open('data_cache.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_output_cache():
    """Load output cache"""
    if os.path.exists('output_cache.json'):
        with open('output_cache.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_output_cache(cache):
    """Save output cache"""
    with open('output_cache.json', 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def fetch_url_content(url):
    """Fetch content from URL"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error fetching URL: {str(e)}"

def process_legal_checks(customer_id, data_cache, output_cache):
    """Process legal compliance checks for a customer"""

    # Get customer entry from output cache
    if customer_id not in output_cache:
        print(f"Warning: Customer {customer_id} not found in output_cache.json")
        return

    customer_entry = output_cache[customer_id]

    # Check if customer has an offer
    offer_decision = customer_entry.get('offer_decision', '')
    if not offer_decision:
        print(f"No offer for {customer_id} - legal check not applicable")
        customer_entry['legal_notes'] = ''
        customer_entry['legal_approved'] = ''
        return

    # Get content to review
    content_title = customer_entry.get('content_title', '')
    content_body = customer_entry.get('content_body', '')

    if not content_title and not content_body:
        print(f"No content for {customer_id} - legal check not applicable")
        customer_entry['legal_notes'] = ''
        customer_entry['legal_approved'] = ''
        return

    # Load legal checks
    legal_checks = data_cache.get('legal_checks', [])

    # Process each legal check - fetch URL content if needed
    processed_checks = []
    for check in legal_checks:
        check_name = check.get('check', '')
        rule = check.get('rule', '')

        # Check if rule is a URL
        if rule.startswith('http://') or rule.startswith('https://'):
            print(f"  Fetching legal rule from URL: {rule}")
            rule_content = fetch_url_content(rule)
            processed_checks.append({
                'check': check_name,
                'rule': rule_content
            })
        else:
            processed_checks.append({
                'check': check_name,
                'rule': rule
            })

    # Get customer data from data_cache
    customers = data_cache.get('all_customers', [])
    customer_data = next((c for c in customers if c.get('customer_id') == customer_id), {})

    # Build prompt for Claude API
    prompt = f"""You are a Legal Compliance Agent reviewing marketing content for regulatory compliance.

CUSTOMER DATA:
{json.dumps(customer_data, indent=2, ensure_ascii=False)}

PROPOSED MARKETING CONTENT:
Title: {content_title}
Body: {content_body}

LEGAL COMPLIANCE CHECKS:
{json.dumps(processed_checks, indent=2, ensure_ascii=False)}

TASK:
Review the proposed marketing content against each legal compliance check. For each check:
1. Evaluate if the content and customer situation comply with the rule
2. Note any violations or concerns

DECISION:
- APPROVE if all checks pass
- REJECT if any legal concern exists

Provide your response in the following JSON format:
{{
  "legal_approved": true or false,
  "legal_notes": "Explanation of decision, listing any violations or concerns. Use newlines (\\n) to separate each check result or violation for readability."
}}
"""

    # Call Claude API
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)

    print(f"  Calling Claude API for legal compliance review...")
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Parse response
    response_text = response.content[0].text

    # Extract JSON from response
    try:
        # Find JSON in response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        json_str = response_text[start_idx:end_idx]
        result = json.loads(json_str)

        legal_approved = result.get('legal_approved', False)
        legal_notes = result.get('legal_notes', '')

        # Update output cache
        customer_entry['legal_notes'] = legal_notes
        customer_entry['legal_approved'] = 'TRUE' if legal_approved else 'FALSE'

        status = "APPROVED" if legal_approved else "REJECTED"
        print(f"{status}: {customer_id}")

    except json.JSONDecodeError as e:
        print(f"Warning: Error parsing API response: {e}")
        customer_entry['legal_notes'] = f"Error: Could not parse legal review response"
        customer_entry['legal_approved'] = 'FALSE'

def main():
    if len(sys.argv) < 2:
        print("Usage: python3.11 run.py <customer_id|all>")
        sys.exit(1)

    arg = sys.argv[1]

    # Load data
    data_cache = load_data_cache()
    output_cache = load_output_cache()

    if arg == 'all':
        # Process all customers
        print("Checking legal compliance for all customers...")
        customers = data_cache.get('all_customers', [])
        for customer in customers:
            customer_id = customer.get('customer_id')
            if customer_id:
                process_legal_checks(customer_id, data_cache, output_cache)
    else:
        # Process single customer
        customer_id = arg
        print(f"Checking legal compliance for customer {customer_id}...")
        process_legal_checks(customer_id, data_cache, output_cache)

    # Save output cache
    save_output_cache(output_cache)
    print(f"\nLegal compliance results written to output_cache.json")

if __name__ == '__main__':
    main()

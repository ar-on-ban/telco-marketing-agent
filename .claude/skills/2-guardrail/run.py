#!/usr/bin/env python3.11
"""
Check if customer contact should be blocked by guardrails
"""
import json
import sys
from pathlib import Path

def check_guardrails(customer_id, cache_data, output_cache):
    """Check guardrails for a single customer"""
    print(f"\nChecking guardrails for customer {customer_id}...")

    # Find customer record
    customer = None
    for c in cache_data['all_customers']:
        if c['customer_id'] == customer_id:
            customer = c
            break

    if not customer:
        print(f"Error: Customer {customer_id} not found")
        return None

    # Check if customer entry exists in output_cache
    if customer_id not in output_cache:
        print(f"Warning: No analysis found for {customer_id}. Run /1-analyze first.")
        return None

    customer_output = output_cache[customer_id]

    # Check if customer has a trigger
    has_trigger = customer_output.get('has_trigger', 'FALSE') == 'TRUE'

    if not has_trigger:
        # No trigger - leave guardrail fields empty
        print(f"No trigger detected - guardrails not applicable")
        return {
            "guardrail_notes": "",
            "guardrail_approved": ""
        }

    # Customer has trigger - check blocking conditions
    blocking_reasons = []

    # Check 1: active_billing_dispute
    active_dispute = customer.get('active_billing_dispute', 'FALSE')
    if active_dispute == 'TRUE':
        blocking_reasons.append("Active billing dispute")

    # Check 2: days_since_last_contact < 7
    days_since_contact = customer.get('days_since_last_contact', '999')
    try:
        days_since_contact = float(days_since_contact)
    except (ValueError, TypeError):
        days_since_contact = 999
    if days_since_contact < 7:
        blocking_reasons.append(f"Recently contacted ({int(days_since_contact)} days ago)")

    # Determine approval
    if blocking_reasons:
        approved = "FALSE"
        notes = f"BLOCKED: {', '.join(blocking_reasons)}"
        print(f"Contact blocked: {', '.join(blocking_reasons)}")
    else:
        approved = "TRUE"
        notes = "All guardrail checks passed"
        print(f"Contact approved")

    return {
        "guardrail_notes": notes,
        "guardrail_approved": approved
    }

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3.11 run.py <customer_id|all>")
        sys.exit(1)

    target = sys.argv[1]

    # Load cache data
    cache_path = Path("data_cache.json")
    if not cache_path.exists():
        print("Error: data_cache.json not found. Run /0-load-data first.")
        sys.exit(1)

    with open(cache_path, 'r', encoding='utf-8') as f:
        cache_data = json.load(f)

    # Load output cache
    output_cache_path = Path("output_cache.json")
    if not output_cache_path.exists():
        print("Error: output_cache.json not found. Run /1-analyze first.")
        sys.exit(1)

    with open(output_cache_path, 'r', encoding='utf-8') as f:
        output_cache = json.load(f)

    # Process customer(s)
    if target == "all":
        customer_ids = [c['customer_id'] for c in cache_data['all_customers']]
        print(f"Checking guardrails for all {len(customer_ids)} customers...")
    else:
        customer_ids = [target]

    # Check guardrails for each customer
    for customer_id in customer_ids:
        result = check_guardrails(customer_id, cache_data, output_cache)
        if result:
            # Initialize customer entry if needed
            if customer_id not in output_cache:
                output_cache[customer_id] = {}
            # Update with guardrail results
            output_cache[customer_id].update(result)

    # Write output cache
    with open(output_cache_path, 'w', encoding='utf-8') as f:
        json.dump(output_cache, f, ensure_ascii=False, indent=2)

    print(f"\nGuardrail results written to {output_cache_path}")
    if target == "all":
        print(f"  Processed {len(customer_ids)} customers")

if __name__ == "__main__":
    main()

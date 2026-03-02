#!/usr/bin/env python3.11
"""
Recommend an appropriate product offer based on trigger and intent
"""
import json
import os
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def recommend_offer(customer_id, cache_data, output_cache):
    """Recommend offer for a single customer"""
    print(f"\nRecommending offer for customer {customer_id}...")

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
        print(f"Warning: No analysis found for {customer_id}. Run prior steps first.")
        return None

    customer_output = output_cache[customer_id]

    # Check guardrail approval
    guardrail_approved = customer_output.get('guardrail_approved', '')
    if guardrail_approved != 'TRUE':
        print(f"No offer (guardrail not approved)")
        return {
            "offer_decision": ""
        }

    # Build prompt for Claude API
    workflow_examples_text = "\n\n".join([
        f"Customer Signals: {ex.get('customer_signals', '')}\n"
        f"Trigger Detection: {ex.get('trigger_detection', '')}\n"
        f"Intent Inference: {ex.get('intent_inference', '')}\n"
        f"Offer Decision: {ex.get('offer_decision', '')}"
        for ex in cache_data['workflow_examples'] if ex.get('customer_signals')
    ])

    prompt = f"""You are recommending a telecom product offer for a customer based on their trigger and intent.

**Business Directive:**
{cache_data.get('business_directive', 'Recommend products that match customer needs and provide clear value.')}

**Customer Record:**
{json.dumps(customer, indent=2, ensure_ascii=False)}

**Customer Analysis:**
- Trigger Reason: {customer_output.get('trigger_reason', '')}
- Customer Intent: {customer_output.get('customer_intent', '')}

**Product Catalog:**

Mobile Plans:
- Prepaid Basic: Prepaid plan for budget-conscious customers
- Prepaid Plus: Enhanced prepaid with more features
- Postpaid S: Entry-level postpaid (smaller data allowance)
- Postpaid M: Mid-tier postpaid (balanced data and voice)
- Postpaid L: Premium postpaid (large data allowance)
- Family Plan: Family plan with multiple lines

Home Internet:
- Home Internet Basic: Basic internet package
- Home Internet 500: 500 Mbps download speed
- Home Internet 1000: 1000 Mbps download speed (premium)

Add-ons:
- Extra data pack: Additional data packages
- EU roaming pack: International roaming package
- Device insurance: Device protection plan
- Streaming bundle: Streaming service bundles
- Cloud storage: Cloud storage add-on

**Workflow Examples:**
Study these examples to understand how triggers and intents inform product recommendations:

{workflow_examples_text}

**Your Task:**
Based on the customer's trigger reason and intent, recommend the most appropriate product or offer. Consider:
1. The customer's current plan and usage patterns
2. The specific pain point or opportunity identified in the trigger
3. Products that directly address the customer's inferred intent
4. Value proposition that matches their needs

**Output Format:**
Provide your recommendation as a simple string with the product name and brief rationale.

Example: "Home Internet 1000 upgrade - addresses slow internet speed complaints and high mobile data usage"

Keep it concise (1-2 sentences maximum)."""

    # Call Claude API
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        offer_decision = message.content[0].text.strip()

        # Build output record
        output = {
            "offer_decision": offer_decision
        }

        print(f"Offer recommended: {offer_decision[:80]}...")
        return output

    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return None

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
        print("Error: output_cache.json not found. Run prior steps first.")
        sys.exit(1)

    with open(output_cache_path, 'r', encoding='utf-8') as f:
        output_cache = json.load(f)

    # Process customer(s)
    if target == "all":
        customer_ids = [c['customer_id'] for c in cache_data['all_customers']]
        print(f"Recommending offers for all {len(customer_ids)} customers...")
    else:
        customer_ids = [target]

    # Recommend offer for each customer
    for customer_id in customer_ids:
        result = recommend_offer(customer_id, cache_data, output_cache)
        if result:
            # Initialize customer entry if needed
            if customer_id not in output_cache:
                output_cache[customer_id] = {}
            # Update with offer recommendation
            output_cache[customer_id].update(result)

    # Write output cache
    with open(output_cache_path, 'w', encoding='utf-8') as f:
        json.dump(output_cache, f, ensure_ascii=False, indent=2)

    print(f"\nOffer recommendations written to {output_cache_path}")
    if target == "all":
        print(f"  Processed {len(customer_ids)} customers")

if __name__ == "__main__":
    main()

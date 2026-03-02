#!/usr/bin/env python3.11
"""
Brand compliance sub-agent using good/bad example comparison
"""
import json
import os
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_brand_compliance(customer_id, cache_data, output_cache):
    """Check brand compliance for a single customer"""
    print(f"\nChecking brand compliance for customer {customer_id}...")

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
        print(f"Warning: No prior analysis found for {customer_id}.")
        return None

    customer_output = output_cache[customer_id]

    # Check if offer was recommended
    offer_decision = customer_output.get('offer_decision', '')
    if not offer_decision:
        print(f"No brand check (no offer)")
        return {
            "brand_notes": "",
            "brand_approved": ""
        }

    # Get content to review
    content_body = customer_output.get('content_body', '')
    content_title = customer_output.get('content_title', '')

    # Get brand examples
    brand_examples = cache_data.get('brand_examples', [])

    # Build prompt for Claude API
    brand_examples_text = "\n\n".join([
        f"**{ex.get('team', 'Example')}**\n"
        f"Good Example: {ex.get('good_example', '')}\n"
        f"Bad Example: {ex.get('bad_example', '')}"
        for ex in brand_examples if ex.get('good_example') or ex.get('bad_example')
    ])

    prompt = f"""You are a Brand Compliance Sub-Agent reviewing marketing content against brand guidelines.

**Marketing Content to Review:**
Title: {content_title}
Body: {content_body}

**Brand Guidelines - Good vs Bad Examples:**

{brand_examples_text}

**Your Task:**
Compare the generated content against the good and bad examples:

1. **Good examples** show what to emulate - professional tone, clear language, customer-focused messaging
2. **Bad examples** show what to avoid - aggressive language, unclear messaging, technical jargon

Evaluate:
- Tone and style
- Language quality and clarity
- Customer focus vs aggressive sales tactics
- Professionalism

**Output Format:**
Return ONLY valid JSON with no additional text:
{{
  "approved": true or false,
  "notes": "Explanation referencing which good/bad examples influenced the decision. Use newlines (\\n) to separate distinct observations for readability."
}}

APPROVE if content reflects qualities of good examples.
REJECT if content resembles bad examples.

Review now:"""

    # Call Claude API
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # Parse JSON response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1

        if start_idx == -1 or end_idx == 0:
            print(f"Error: Could not find JSON in response")
            print(f"Response: {response_text[:200]}")
            return None

        json_str = response_text[start_idx:end_idx]
        result = json.loads(json_str)

        # Build output record
        output = {
            "brand_notes": result.get("notes", ""),
            "brand_approved": "TRUE" if result.get("approved", False) else "FALSE"
        }

        print(f"Brand review complete: {output['brand_approved']}")
        return output

    except Exception as e:
        print(f"Error calling Claude API: {e}")
        import traceback
        traceback.print_exc()
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
        print(f"Checking brand compliance for all {len(customer_ids)} customers...")
    else:
        customer_ids = [target]

    # Check brand compliance for each customer
    for customer_id in customer_ids:
        result = check_brand_compliance(customer_id, cache_data, output_cache)
        if result:
            # Initialize customer entry if needed
            if customer_id not in output_cache:
                output_cache[customer_id] = {}
            # Update with brand review
            output_cache[customer_id].update(result)

    # Write output cache
    with open(output_cache_path, 'w', encoding='utf-8') as f:
        json.dump(output_cache, f, ensure_ascii=False, indent=2)

    print(f"\nBrand compliance results written to {output_cache_path}")
    if target == "all":
        print(f"  Processed {len(customer_ids)} customers")

if __name__ == "__main__":
    main()

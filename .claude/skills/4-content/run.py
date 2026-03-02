#!/usr/bin/env python3.11
"""
Generate marketing content for the customer
"""
import json
import os
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_content(customer_id, cache_data, output_cache):
    """Generate content for a single customer"""
    print(f"\nGenerating content for customer {customer_id}...")

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
        print(f"No content (no offer recommended)")
        return {
            "channel": "",
            "content_title": "",
            "content_body": ""
        }

    # Get preferred channel from customer data
    preferred_channel = customer.get('preferred_channel', 'email')
    # Parse preferred channels (might be comma-separated)
    if ',' in preferred_channel:
        preferred_channel = preferred_channel.split(',')[0].strip()

    # Build prompt for Claude API
    workflow_examples_text = "\n\n".join([
        f"Customer Signals: {ex.get('customer_signals', '')}\n"
        f"Trigger: {ex.get('trigger_detection', '')}\n"
        f"Intent: {ex.get('intent_inference', '')}\n"
        f"Offer: {ex.get('offer_decision', '')}\n"
        f"Sample Content: {ex.get('generated_content_sample', '')}"
        for ex in cache_data['workflow_examples'] if ex.get('customer_signals')
    ])

    prompt = f"""You are generating marketing content for a telecom customer.

**Business Directive:**
{cache_data.get('business_directive', 'Create personalized, relevant marketing communications.')}

**Content Tone Guidelines:**
{cache_data.get('content_tone', 'Professional, friendly, and customer-focused.')}

**Customer Record:**
{json.dumps(customer, indent=2, ensure_ascii=False)}

**Offer Decision:**
{offer_decision}

**Preferred Channel:**
{preferred_channel}

**Channel Format Requirements:**
- `app`: Push notification with LESS than 100 characters, use a few emojis
- `email`: Email subject and body with MINIMUM 350 characters
- `call`: Phone script for agent with MINIMUM 500 characters
- `text`: WhatsApp, Messenger, or SMS with LESS than 200 characters

**Workflow Examples:**
Study these to understand expected tone and structure:

{workflow_examples_text}

**Your Task:**
Generate marketing content for the "{preferred_channel}" channel that:
1. Addresses the customer's specific situation
2. Presents the offer in a compelling way
3. Follows the appropriate format for the channel
4. Matches the content tone guidelines

**Output Format:**
Return ONLY valid JSON with no additional text:
{{
  "channel": "{preferred_channel}",
  "title": "Title or subject line",
  "body": "Message content"
}}

For app/text channels, the title should be empty or very short.
For email, the title is the subject line.
For call, the title is a brief script header and body is the full script.

Generate the content now:"""

    # Call Claude API
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
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
            "channel": result.get("channel", preferred_channel),
            "content_title": result.get("title", ""),
            "content_body": result.get("body", "")
        }

        print(f"Content generated for {output['channel']} channel")
        print(f"  Title: {output['content_title'][:60]}...")
        print(f"  Body length: {len(output['content_body'])} chars")
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
        print(f"Generating content for all {len(customer_ids)} customers...")
    else:
        customer_ids = [target]

    # Generate content for each customer
    for customer_id in customer_ids:
        result = generate_content(customer_id, cache_data, output_cache)
        if result:
            # Initialize customer entry if needed
            if customer_id not in output_cache:
                output_cache[customer_id] = {}
            # Update with content
            output_cache[customer_id].update(result)

    # Write output cache
    with open(output_cache_path, 'w', encoding='utf-8') as f:
        json.dump(output_cache, f, ensure_ascii=False, indent=2)

    print(f"\nContent written to {output_cache_path}")
    if target == "all":
        print(f"  Processed {len(customer_ids)} customers")

if __name__ == "__main__":
    main()

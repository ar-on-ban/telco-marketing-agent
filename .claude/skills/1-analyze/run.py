#!/usr/bin/env python3.11
"""
Analyze customer to detect marketing triggers and infer intent
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def calculate_aggregate_stats(all_customers):
    """Calculate aggregate statistics for comparison"""
    if not all_customers:
        return {}

    def to_num(val, default=0):
        """Convert string to number safely"""
        if isinstance(val, (int, float)):
            return val
        try:
            return float(val) if val else default
        except (ValueError, TypeError):
            return default

    # Calculate averages
    total_customers = len(all_customers)
    avg_age = sum(to_num(c.get('age', 0)) for c in all_customers) / total_customers
    avg_tenure = sum(to_num(c.get('tenure_months', 0)) for c in all_customers) / total_customers
    avg_churn_risk = sum(to_num(c.get('churn_risk_score', 0)) for c in all_customers) / total_customers
    avg_device_age = sum(to_num(c.get('device_age_months', 0)) for c in all_customers) / total_customers
    avg_data_usage = sum(to_num(c.get('avg_monthly_data_gb', 0)) for c in all_customers) / total_customers
    avg_support_tickets = sum(to_num(c.get('support_tickets_12m', 0)) for c in all_customers) / total_customers

    return {
        "total_customers": total_customers,
        "avg_age": round(avg_age, 1),
        "avg_tenure_months": round(avg_tenure, 1),
        "avg_churn_risk_score": round(avg_churn_risk, 2),
        "avg_device_age_months": round(avg_device_age, 1),
        "avg_monthly_data_gb": round(avg_data_usage, 1),
        "avg_support_tickets_12m": round(avg_support_tickets, 1)
    }

def analyze_customer(customer_id, cache_data):
    """Analyze a single customer"""
    print(f"\nAnalyzing customer {customer_id}...")

    # Find customer record
    customer = None
    for c in cache_data['all_customers']:
        if c['customer_id'] == customer_id:
            customer = c
            break

    if not customer:
        print(f"Error: Customer {customer_id} not found")
        return None

    # Calculate aggregate stats
    aggregate_stats = calculate_aggregate_stats(cache_data['all_customers'])

    # Build prompt for Claude API
    workflow_examples_text = "\n\n".join([
        f"Customer Signals: {ex.get('customer_signals', '')}\n"
        f"Trigger Detection: {ex.get('trigger_detection', '')}\n"
        f"Intent Inference: {ex.get('intent_inference', '')}\n"
        f"Offer Decision: {ex.get('offer_decision', '')}"
        for ex in cache_data['workflow_examples'] if ex.get('customer_signals')
    ])

    prompt = f"""You are analyzing a telecom customer to detect if there's a meaningful marketing trigger to contact them now.

**Business Directive:**
{cache_data.get('business_directive', 'Provide personalized, relevant marketing communications to customers at the right time.')}

**Customer Record:**
{json.dumps(customer, indent=2, ensure_ascii=False)}

**Aggregate Statistics (for comparison):**
{json.dumps(aggregate_stats, indent=2)}

**Workflow Examples:**
Study these examples to understand the reasoning depth and approach expected. Apply similar thinking patterns to this customer's unique situation:

{workflow_examples_text}

**Your Task:**
1. Analyze ALL customer data to detect if there's a meaningful trigger to contact them now
2. Compare customer metrics against aggregate statistics to identify outliers
3. Infer the customer's intent based on their behavior patterns and current situation

**Output Format:**
Provide your analysis in JSON format with these exact fields:
{{
  "has_trigger": "TRUE" or "FALSE",
  "trigger_reason": "Detailed explanation of the trigger (or why there's no trigger). Use newlines (\\n) to separate distinct points for readability.",
  "customer_intent": "Inferred intent based on customer behavior and situation. Use newlines (\\n) to separate distinct points for readability."
}}

Be specific and reference actual data points from the customer record. If there's no meaningful trigger, explain why clearly."""

    # Call Claude API
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # Parse JSON response
        # Find JSON block in response
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
            "customer_id": customer_id,
            "timestamp": datetime.now().isoformat(),
            "has_trigger": result.get("has_trigger", "FALSE"),
            "trigger_reason": result.get("trigger_reason", ""),
            "customer_intent": result.get("customer_intent", "")
        }

        print(f"Analysis complete: has_trigger={output['has_trigger']}")
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

    # Load or initialize output cache
    output_cache_path = Path("output_cache.json")
    if output_cache_path.exists():
        with open(output_cache_path, 'r', encoding='utf-8') as f:
            output_cache = json.load(f)
    else:
        output_cache = {}

    # Process customer(s)
    if target == "all":
        customer_ids = [c['customer_id'] for c in cache_data['all_customers']]
        print(f"Analyzing all {len(customer_ids)} customers...")
    else:
        customer_ids = [target]

    # Analyze each customer
    for customer_id in customer_ids:
        result = analyze_customer(customer_id, cache_data)
        if result:
            # Initialize customer entry if needed
            if customer_id not in output_cache:
                output_cache[customer_id] = {}
            # Update with analysis results
            output_cache[customer_id].update(result)

    # Write output cache
    with open(output_cache_path, 'w', encoding='utf-8') as f:
        json.dump(output_cache, f, ensure_ascii=False, indent=2)

    print(f"\nResults written to {output_cache_path}")
    if target == "all":
        print(f"  Processed {len(customer_ids)} customers")

if __name__ == "__main__":
    main()

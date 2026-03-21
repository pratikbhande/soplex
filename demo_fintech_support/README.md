# Soplex Fintech Support Demo

This demo is designed specifically for UK fintech companies and AI agent workflow startups (like Gradient Labs) who need to handle high-volume customer support automation without sacrificing strict compliance or dealing with enormous LLM inference costs.

## What it does
The `fintech_support.sop` file models a standard unauthorized transaction dispute flow. 
Instead of sending every step directly to a massive LLM (which is slow, expensive, and risks hallucination), the Soplex execution graph routes:
- **Conversation** to the LLM (Greeting, Identity verification prompts).
- **Business Logic** to deterministic code (Checking if transaction > 60 days, checking risk score).
- **Actions** to fast function calls (Issuing provisional credit).

## How to run
1. Install soplex: `pip install -e .`
2. Run the analysis demo:
   ```bash
   python demo_fintech_support/demo.py
   ```
3. Test the interactive agent:
   ```bash
   soplex compile demo_fintech_support/fintech_support.sop --output compiled/
   soplex chat compiled/fintech_support.json
   ```

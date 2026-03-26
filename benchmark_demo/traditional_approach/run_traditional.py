#!/usr/bin/env python3
"""
Traditional Pure-LLM Approach Demo
Simulates how traditional AI agents would handle the enterprise KYC process
by calling LLM for every single step including simple logic decisions.
"""

import time
import json
import os
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class LLMCall:
    step: str
    prompt: str
    estimated_tokens: int
    estimated_cost: float
    response_time: float

class TraditionalAgent:
    def __init__(self):
        self.llm_calls: List[LLMCall] = []
        self.total_cost = 0.0
        self.total_tokens = 0
        self.start_time = time.time()

        # Simulated API costs (per 1k tokens)
        self.gpt4_input_cost = 0.03  # $0.03 per 1k input tokens
        self.gpt4_output_cost = 0.06  # $0.06 per 1k output tokens

    def simulate_llm_call(self, step: str, prompt: str, expected_tokens: int) -> str:
        """Simulate an LLM API call with realistic timing and costs"""

        # Simulate API latency (200-800ms)
        latency = 0.2 + (len(prompt) / 1000) * 0.6
        time.sleep(latency)

        # Calculate estimated costs
        input_tokens = len(prompt.split()) * 1.3  # Approximate tokenization
        output_tokens = expected_tokens

        cost = (input_tokens * self.gpt4_input_cost / 1000) + \
               (output_tokens * self.gpt4_output_cost / 1000)

        self.llm_calls.append(LLMCall(
            step=step,
            prompt=prompt[:100] + "..." if len(prompt) > 100 else prompt,
            estimated_tokens=int(input_tokens + output_tokens),
            estimated_cost=cost,
            response_time=latency
        ))

        self.total_cost += cost
        self.total_tokens += int(input_tokens + output_tokens)

        print(f"🧠 [LLM CALL] {step}")
        print(f"   Tokens: {int(input_tokens + output_tokens):,} | Cost: ${cost:.4f} | Time: {latency:.2f}s")

        # Return simulated response based on step
        return self._generate_simulated_response(step)

    def _generate_simulated_response(self, step: str) -> str:
        """Generate realistic responses for demo purposes"""
        responses = {
            "greet_and_collect": "Hello! I'd be happy to help you with KYC onboarding. Please provide your UK Company Registration Number.",
            "validate_format": "The company registration number format is valid.",
            "lookup_company": "Company found: TechCorp Ltd, Status: Active, Incorporated: 2020-03-15",
            "check_status": "The company status is Active and incorporation date is over 6 months ago.",
            "extract_directors": "Directors extracted: John Smith (Director), Jane Doe (Secretary)",
            "verify_representative": "Please upload your ID document for verification.",
            "check_director_match": "Verified representative matches active director John Smith.",
            "calculate_risk": "Risk score calculated: 45 (Low-Medium risk based on fintech sector)",
            "aml_screening": "AML screening complete: No sanctions matches found.",
            "request_address": "Please upload proof of business address (utility bill or bank statement).",
            "validate_address": "Business address verified and matches registered office.",
            "bank_statements": "Please upload bank statements for the last 3 months.",
            "analyze_statements": "Bank statement analysis complete: No unusual patterns detected.",
            "final_approval": "Final approval score: 92 - Account approved for onboarding.",
            "generate_welcome": "Welcome package generated with account details.",
            "confirm_completion": "KYC onboarding completed successfully! Your account is now active.",
        }
        return responses.get(step, "Processing complete.")

def run_traditional_kyc_demo():
    print("=" * 60)
    print("🏛️  TRADITIONAL PURE-LLM APPROACH DEMO")
    print("Every step requires an LLM call - even simple logic!")
    print("=" * 60)

    agent = TraditionalAgent()

    # Simulate the full KYC process with LLM calls for EVERY step
    steps = [
        ("greet_and_collect", "You are a KYC onboarding assistant. Greet the client and ask for their UK Company Registration Number. Be professional and friendly.", 50),
        ("validate_format", "Check if this UK company registration number '12345678' follows the correct format. Explain your validation process.", 80),
        ("lookup_company", "Query the Companies House database for company '12345678' and return the company details including status and incorporation date.", 120),
        ("check_status", "Review this company data: 'TechCorp Ltd, Status: Active, Incorporated: 2020-03-15'. Determine if it meets our criteria for onboarding (Active status, over 6 months old).", 100),
        ("extract_directors", "Extract the list of directors from this Companies House data and format them clearly for verification purposes.", 90),
        ("verify_representative", "Ask the customer representative to verify their identity by uploading identification documents. Explain the verification process.", 70),
        ("check_director_match", "Compare the verified identity 'John Smith' against our extracted directors list to confirm they are authorized to act for the company.", 85),
        ("calculate_risk", "Calculate a risk score for company 'TechCorp Ltd' in the fintech sector with £2M annual turnover, incorporated in UK. Use our risk assessment criteria.", 150),
        ("aml_screening", "Screen company 'TechCorp Ltd' and director 'John Smith' against UK PEP lists, sanctions databases, and watchlists. Report any matches.", 140),
        ("request_address", "Request that the customer upload proof of business address documentation. Explain what documents are acceptable.", 60),
        ("validate_address", "Verify that the uploaded business address proof matches the Companies House registered office address. Confirm validation.", 95),
        ("bank_statements", "Ask the customer to upload the last 3 months of bank statements for source of funds verification. Explain why this is required.", 75),
        ("analyze_statements", "Analyze the uploaded bank statements for unusual transaction patterns, high-risk jurisdictions, or suspicious activities. Provide assessment.", 180),
        ("final_approval", "Calculate the final onboarding approval score combining: risk score (45), AML clear, address verified, statements clean. Determine approval.", 120),
        ("generate_welcome", "Generate a welcome package for the approved customer including account details and next steps for activation.", 85),
        ("confirm_completion", "Confirm with the customer that their KYC onboarding is complete and their account is now active. Thank them for their patience.", 65),
    ]

    print(f"\n🚀 Starting Traditional KYC Process ({len(steps)} LLM calls required)\n")

    for i, (step, prompt, tokens) in enumerate(steps, 1):
        print(f"Step {i}/{len(steps)}: {step.replace('_', ' ').title()}")
        response = agent.simulate_llm_call(step, prompt, tokens)
        print(f"   Response: {response}\n")

    # Calculate final metrics
    end_time = time.time()
    total_time = end_time - agent.start_time

    print("=" * 60)
    print("📊 TRADITIONAL APPROACH RESULTS")
    print("=" * 60)
    print(f"Total LLM Calls:     {len(agent.llm_calls)}")
    print(f"Total Tokens:        {agent.total_tokens:,}")
    print(f"Total Cost:          ${agent.total_cost:.4f}")
    print(f"Total Time:          {total_time:.2f} seconds")
    print(f"Average per call:    ${agent.total_cost/len(agent.llm_calls):.4f}")
    print(f"Processing overhead: High (LLM for simple logic)")
    print(f"Accuracy risk:       High (LLM hallucination on decisions)")

    # Save results for comparison
    results = {
        "approach": "traditional_pure_llm",
        "total_llm_calls": len(agent.llm_calls),
        "total_tokens": agent.total_tokens,
        "total_cost": agent.total_cost,
        "total_time": total_time,
        "avg_cost_per_call": agent.total_cost / len(agent.llm_calls),
        "accuracy_risk": "high",
        "processing_overhead": "high"
    }

    os.makedirs("../results", exist_ok=True)
    with open("../results/traditional_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Results saved to ../results/traditional_results.json")
    return results

if __name__ == "__main__":
    run_traditional_kyc_demo()
#!/usr/bin/env python3
"""
Soplex Hybrid Approach Demo
Shows how soplex optimizes costs by using LLMs only for conversation
and deterministic code for logic, decisions, and API calls.
"""

import time
import json
import os
from typing import Dict, List
from dataclasses import dataclass
from soplex import PythonGraphBuilder

@dataclass
class ExecutionStep:
    step: str
    type: str  # "llm", "code", "api"
    cost: float
    time: float
    description: str

class SoplexAgent:
    def __init__(self):
        self.execution_log: List[ExecutionStep] = []
        self.total_cost = 0.0
        self.llm_calls = 0
        self.code_calls = 0
        self.start_time = time.time()

        # Cost structure (much lower for code execution)
        self.gpt4_input_cost = 0.03   # $0.03 per 1k input tokens
        self.gpt4_output_cost = 0.06  # $0.06 per 1k output tokens
        self.code_execution_cost = 0.0001  # Virtually free

    def execute_llm_step(self, step: str, description: str, estimated_tokens: int) -> Dict:
        """Execute conversational step using LLM"""
        latency = 0.2 + (estimated_tokens / 1000) * 0.4
        time.sleep(latency)

        # Calculate cost (only for conversational steps)
        cost = (estimated_tokens * self.gpt4_input_cost / 1000) + \
               (estimated_tokens * 0.5 * self.gpt4_output_cost / 1000)

        self.execution_log.append(ExecutionStep(
            step=step,
            type="llm",
            cost=cost,
            time=latency,
            description=description
        ))

        self.total_cost += cost
        self.llm_calls += 1

        print(f"🧠 [LLM STEP] {step}")
        print(f"   Cost: ${cost:.4f} | Time: {latency:.2f}s | {description}")

        return {"success": True, "response": self._get_llm_response(step)}

    def execute_code_step(self, step: str, description: str, logic_func) -> Dict:
        """Execute deterministic code logic"""
        start = time.time()

        # Simulate code execution (very fast)
        result = logic_func()
        execution_time = time.time() - start + 0.001  # Minimal overhead

        self.execution_log.append(ExecutionStep(
            step=step,
            type="code",
            cost=self.code_execution_cost,
            time=execution_time,
            description=description
        ))

        self.total_cost += self.code_execution_cost
        self.code_calls += 1

        print(f"⚡ [CODE STEP] {step}")
        print(f"   Cost: ${self.code_execution_cost:.6f} | Time: {execution_time:.3f}s | {description}")

        return {"success": True, "result": result}

    def execute_api_step(self, step: str, description: str, api_func) -> Dict:
        """Execute API call with deterministic logic"""
        start = time.time()

        # Simulate API call
        result = api_func()
        execution_time = time.time() - start + 0.050  # API latency

        self.execution_log.append(ExecutionStep(
            step=step,
            type="api",
            cost=self.code_execution_cost,  # API calls are code-driven
            time=execution_time,
            description=description
        ))

        self.total_cost += self.code_execution_cost
        self.code_calls += 1

        print(f"🔌 [API STEP] {step}")
        print(f"   Cost: ${self.code_execution_cost:.6f} | Time: {execution_time:.3f}s | {description}")

        return {"success": True, "result": result}

    def _get_llm_response(self, step: str) -> str:
        """Simulated LLM responses for conversational steps only"""
        responses = {
            "greet_customer": "Hello! I'm here to help you with KYC onboarding. May I please have your UK Company Registration Number?",
            "request_identity": "Thank you! Now I need to verify your identity. Please upload a government-issued ID document.",
            "request_documents": "Perfect! For the final step, please upload proof of your business address - a recent utility bill or bank statement.",
            "confirm_completion": "Excellent! Your KYC verification is now complete. Your account has been activated and you should receive a welcome email shortly.",
            "escalation_notice": "I need to transfer your case to our compliance team for additional review. You'll receive an update within 24 hours."
        }
        return responses.get(step, "Step completed successfully.")

def run_soplex_kyc_demo():
    print("=" * 60)
    print("🚀 SOPLEX HYBRID APPROACH DEMO")
    print("LLM for conversation, Code for logic & APIs")
    print("=" * 60)

    agent = SoplexAgent()

    print(f"\n🏗️ Building Hybrid Execution Graph\n")

    # Step 1: LLM - Conversational greeting
    agent.execute_llm_step(
        "greet_customer",
        "Greet customer and collect company registration number",
        120
    )

    # Step 2: CODE - Format validation (no LLM needed!)
    agent.execute_code_step(
        "validate_format",
        "Validate UK company number format using regex",
        lambda: {"valid": True, "format": "########"}
    )

    # Step 3: API - Companies House lookup (deterministic)
    agent.execute_api_step(
        "companies_house_lookup",
        "Query Companies House API for company details",
        lambda: {
            "company_name": "TechCorp Ltd",
            "status": "Active",
            "incorporated": "2020-03-15",
            "directors": ["John Smith", "Jane Doe"]
        }
    )

    # Step 4: CODE - Status validation logic
    agent.execute_code_step(
        "validate_company_status",
        "Check if company is active and meets age requirements",
        lambda: {"eligible": True, "age_months": 48, "status_ok": True}
    )

    # Step 5: CODE - Extract and process director information
    agent.execute_code_step(
        "process_directors",
        "Extract directors list and prepare for verification",
        lambda: {"directors": ["John Smith", "Jane Doe"], "count": 2}
    )

    # Step 6: LLM - Request identity verification (conversational)
    agent.execute_llm_step(
        "request_identity",
        "Ask representative to provide identity verification",
        80
    )

    # Step 7: API - Identity verification service
    agent.execute_api_step(
        "verify_identity",
        "Call Experian/Equifax API for identity verification",
        lambda: {"verified": True, "confidence": 0.95, "name": "John Smith"}
    )

    # Step 8: CODE - Match verification against directors
    agent.execute_code_step(
        "match_director",
        "Verify identity matches company director list",
        lambda: {"is_director": True, "match_confidence": 0.98}
    )

    # Step 9: CODE - Calculate risk score
    agent.execute_code_step(
        "calculate_risk",
        "Calculate company risk score based on sector/turnover",
        lambda: {"risk_score": 45, "risk_level": "medium", "eligible": True}
    )

    # Step 10: API - AML/PEP screening
    agent.execute_api_step(
        "aml_screening",
        "Screen against UK PEP and sanctions databases",
        lambda: {"pep_match": False, "sanctions_match": False, "clear": True}
    )

    # Step 11: LLM - Request address documentation (conversational)
    agent.execute_llm_step(
        "request_documents",
        "Ask customer to upload business address proof",
        70
    )

    # Step 12: API - Document validation service
    agent.execute_api_step(
        "validate_address",
        "Validate uploaded address documents",
        lambda: {"valid": True, "matches_registered": True}
    )

    # Step 13: CODE - Final approval calculation
    agent.execute_code_step(
        "final_approval",
        "Calculate final approval score from all factors",
        lambda: {"approval_score": 92, "approved": True, "auto_approve": True}
    )

    # Step 14: CODE - Generate account details
    agent.execute_code_step(
        "generate_account",
        "Generate account number and setup customer profile",
        lambda: {"account_number": "UK789123456", "profile_created": True}
    )

    # Step 15: LLM - Confirmation message (conversational)
    agent.execute_llm_step(
        "confirm_completion",
        "Confirm successful onboarding and provide next steps",
        90
    )

    # Calculate final metrics
    end_time = time.time()
    total_time = end_time - agent.start_time

    print("\n" + "=" * 60)
    print("📊 SOPLEX HYBRID RESULTS")
    print("=" * 60)
    print(f"Total LLM Calls:     {agent.llm_calls} (conversational only)")
    print(f"Total Code/API:      {agent.code_calls} (logic & data)")
    print(f"Total Cost:          ${agent.total_cost:.4f}")
    print(f"Total Time:          {total_time:.2f} seconds")
    print(f"Processing overhead: Minimal (code for logic)")
    print(f"Accuracy risk:       Minimal (deterministic decisions)")

    # Cost breakdown
    llm_cost = sum(step.cost for step in agent.execution_log if step.type == "llm")
    code_cost = sum(step.cost for step in agent.execution_log if step.type in ["code", "api"])

    print(f"\n💰 Cost Breakdown:")
    print(f"   LLM costs:        ${llm_cost:.4f} ({(llm_cost/agent.total_cost*100):.1f}%)")
    print(f"   Code/API costs:   ${code_cost:.6f} ({(code_cost/agent.total_cost*100):.1f}%)")

    # Save results for comparison
    results = {
        "approach": "soplex_hybrid",
        "total_llm_calls": agent.llm_calls,
        "total_code_calls": agent.code_calls,
        "total_cost": agent.total_cost,
        "total_time": total_time,
        "llm_cost": llm_cost,
        "code_cost": code_cost,
        "accuracy_risk": "minimal",
        "processing_overhead": "minimal",
        "cost_efficiency": "optimized"
    }

    os.makedirs("../results", exist_ok=True)
    with open("../results/soplex_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Results saved to ../results/soplex_results.json")
    return results

if __name__ == "__main__":
    run_soplex_kyc_demo()
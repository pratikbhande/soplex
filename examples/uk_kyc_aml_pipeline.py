import asyncio
import os
import json
from soplex import PythonGraphBuilder

# --- Mock UK APIs ---
def companies_house_check(state: dict) -> dict:
    """Mock Companies House API Check"""
    print("⚡ [CODE EXECUTION] Calling Companies House API...")
    # Simulate API latency
    company_no = state.get("company_number", "12345678")
    is_active = True if company_no != "99999999" else False
    
    # Store outcome in state for branch logic
    state["ch_active"] = is_active
    print(f"   => Result: Active = {is_active}")
    return {"success": True, "state": state}

def identity_verification(state: dict) -> dict:
    """Mock Experian/Equifax API for Director Identity Verification"""
    print("⚡ [CODE EXECUTION] Verifying identity via Experian/Equifax UK...")
    director_id = state.get("director_id", "DIR-001")
    is_verified = True if director_id != "DIR-FRAUD" else False
    
    state["id_verified"] = is_verified
    print(f"   => Result: Verified = {is_verified}")
    return {"success": True, "state": state}

def aml_pep_screening(state: dict) -> dict:
    """Mock AML/PEP and Sanctions screening database"""
    print("⚡ [CODE EXECUTION] Screening against UK FCA Sanctions & PEP DB...")
    director_name = state.get("director_name", "John Doe")
    pep_match = True if director_name.lower() == "pep match" else False
    
    state["pep_match"] = pep_match
    print(f"   => Result: PEP/Sanctions Match = {pep_match}")
    return {"success": True, "state": state}

async def run_pipeline():
    print("==================================================")
    print("🇬🇧 UK Enterprise KYC & AML Onboarding Demo")
    print("Built with soplex PythonGraphBuilder")
    print("==================================================\n")

    # 1. Build the Hybrid Architecture Graph using Python API
    builder = PythonGraphBuilder(name="UK_KYC_AML_Pipeline")

    # Conversation step (LLM)
    builder.add_llm_step(
        id="collect_info",
        action="Greet client and ask for UK Company Registration Number, Director Name, and Director ID"
    )

    # API/Code steps (Deterministic)
    builder.add_code_step(
        id="check_companies_house",
        action="Check Companies House active status",
        handler_func=companies_house_check
    )
    
    builder.add_code_step(
        id="verify_id",
        action="Verify Identity using Experian/Equifax",
        handler_func=identity_verification
    )
    
    builder.add_code_step(
        id="aml_pep_check",
        action="Perform PEP and Sanctions Screening",
        handler_func=aml_pep_screening
    )

    # Branch decisions
    builder.add_branch_step(id="is_active_check", action="Check if company is active")
    builder.add_branch_step(id="is_id_verified", action="Check if ID is verified")
    builder.add_branch_step(id="is_pep_clear", action="Check if PEP screening is clear")

    # End states
    builder.add_end_step(id="end_reject", action="Reject onboarding request")
    builder.add_end_step(id="escalate_compliance", action="Escalate to human compliance officer")
    builder.add_end_step(id="end_success", action="Approve account and notify client")

    # 2. Wire the Nodes into a Graph Pipeline
    
    # Collect Info -> Check CH
    builder.add_edge("collect_info", "check_companies_house")
    
    # Check CH -> Branch(is_active)
    builder.add_edge("check_companies_house", "is_active_check")
    builder.add_edge("is_active_check", "verify_id", condition_func=lambda s: s.get("ch_active") is True)
    builder.add_edge("is_active_check", "end_reject", condition_func=lambda s: s.get("ch_active") is False)
    
    # Verify ID -> Branch(is_verified)
    builder.add_edge("verify_id", "is_id_verified")
    builder.add_edge("is_id_verified", "aml_pep_check", condition_func=lambda s: s.get("id_verified") is True)
    builder.add_edge("is_id_verified", "escalate_compliance", condition_func=lambda s: s.get("id_verified") is False)
    
    # AML Check -> Branch(is_pep)
    builder.add_edge("aml_pep_check", "is_pep_clear")
    builder.add_edge("is_pep_clear", "escalate_compliance", condition_func=lambda s: s.get("pep_match") is True)
    builder.add_edge("is_pep_clear", "end_success", condition_func=lambda s: s.get("pep_match") is False)

    # Provide our mock function mapping to the executor
    code_handlers = {
        "check_companies_house": companies_house_check,
        "verify_id": identity_verification,
        "aml_pep_check": aml_pep_screening
    }

    # 3. Compile and define initial test state
    test_state = {
        "company_number": "12345678",
        "director_id": "DIR-001",
        "director_name": "John Doe"
    }
    graph = builder.build()

    print(f"Graph successfully compiled: {len(graph.nodes)} nodes, {len(graph.edges)} edges.")
    print("Starting pipeline execution (Bypassing interactive chat for test)...\n")
    
    # Manually drive the graph for demo purposes to show code execution
    current_node = "check_companies_house" # Skip LLM step for deterministic demo
    state = test_state
    
    while current_node and "end" not in current_node and "escalate" not in current_node:
        node = graph.nodes[current_node]
        prev_node = current_node
        
        if node.type.value == "code":
            handler = code_handlers[current_node]
            res = handler(state)
            state = res["state"]
            
            # Find next node
            for edge in graph.edges:
                if edge.from_node == current_node:
                    current_node = edge.to_node
                    break
                    
        elif node.type.value == "branch":
            print(f"🔀 [BRANCH DECISION] Evaluating {node.action}...")
            # Find matching edge
            for edge in graph.edges:
                if edge.from_node == current_node:
                    # In our builder, conditions are currently functions, we would eval them.
                    # As PythonGraphBuilder builds python funcs, we must run the matching logic 
                    if edge.condition_type == "custom" and hasattr(edge, 'condition') and edge.condition:
                        if edge.condition(state):
                            print(f"   => Decision routed to: {edge.to_node}")
                            current_node = edge.to_node
                            break
                    else:
                        current_node = edge.to_node
                        break
        
        if current_node == prev_node:
            print(f"🚨 Graph execution stuck at {current_node}. Exiting loop.")
            break
                        
    print(f"\n🎯 [FINAL OUTCOME] The Execution stopped at Node: {current_node}")
    
    # Demo Failure Path
    print("\n\n--- Testing PEP Match Failure Scenario ---")
    state = {
        "company_number": "12345678",
        "director_id": "DIR-001",
        "director_name": "pep match" # Trigger failure
    }
    
    current_node = "check_companies_house"
    while current_node and "end" not in current_node and "escalate" not in current_node:
        node = graph.nodes[current_node]
        prev_node = current_node
        
        if node.type.value == "code":
            handler = code_handlers[current_node]
            res = handler(state)
            state = res["state"]
            for edge in graph.edges:
                if edge.from_node == current_node:
                    current_node = edge.to_node
                    break
        elif node.type.value == "branch":
            print(f"🔀 [BRANCH DECISION] Evaluating {node.action}...")
            for edge in graph.edges:
                if edge.from_node == current_node:
                    if edge.condition_type == "custom" and hasattr(edge, 'condition') and edge.condition:
                        if edge.condition(state):
                            print(f"   => Decision routed to: {edge.to_node}")
                            current_node = edge.to_node
                            break
        
        if current_node == prev_node:
            print(f"🚨 Graph execution stuck at {current_node}. Exiting loop.")
            break
                            
    print(f"\n🚨 [FINAL OUTCOME] The Execution stopped at Node: {current_node} (High Risk Flagged)")

if __name__ == "__main__":
    asyncio.run(run_pipeline())

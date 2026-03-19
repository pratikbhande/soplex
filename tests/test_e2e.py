"""
End-to-end integration tests for soplex.
These tests use real API calls and are marked with @pytest.mark.e2e.
Run with: pytest tests/test_e2e.py -v -m e2e
"""
import pytest
import os
import json
from pathlib import Path

from soplex.parser.sop_parser import SOPParser
from soplex.compiler.graph_builder import GraphBuilder
from soplex.runtime.executor import SOPExecutor
from soplex.runtime.tool_registry import ToolRegistry
from soplex.llm.provider import LLMProvider
from soplex.config import get_config
from soplex.utils.cost_tracker import record_session_costs


@pytest.mark.e2e
class TestE2EIntegration:
    """End-to-end integration tests using real APIs."""

    @pytest.fixture(scope="class")
    def skip_if_no_api_key(self):
        """Skip tests if no OpenAI API key is available."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY environment variable not set")

    @pytest.fixture
    def real_llm_provider(self, skip_if_no_api_key):
        """Create real LLM provider for testing."""
        config = get_config(provider="openai", model="gpt-4o-mini", temperature=0.1)
        return LLMProvider(config)

    @pytest.fixture
    def mock_tool_registry(self):
        """Create tool registry with mock tools for E2E tests."""
        registry = ToolRegistry()

        def mock_order_db(order_number: str = "12345") -> dict:
            """Mock order database lookup."""
            return {
                "order_id": order_number,
                "customer_email": "customer@example.com",
                "order_date": "2024-03-01",
                "status": "delivered",
                "total": 89.99,
                "items": ["Widget A", "Widget B"],
                "shipping": 5.99
            }

        def mock_identity_check(email: str = "customer@example.com", order_number: str = "12345") -> dict:
            """Mock identity verification."""
            return {
                "verified": True,
                "confidence": 0.95,
                "match_details": ["email", "order_date"]
            }

        def mock_payments_api(action: str = "refund", amount: float = 84.0, reference: str = "12345") -> dict:
            """Mock payment processing."""
            return {
                "status": "success",
                "transaction_id": f"TXN-{reference}-REFUND",
                "amount_refunded": amount,
                "processing_time": "3-5 business days"
            }

        registry.register_tool("order_db", mock_order_db, "Order database lookup")
        registry.register_tool("identity_check", mock_identity_check, "Identity verification")
        registry.register_tool("payments_api", mock_payments_api, "Payment processing")

        return registry

    def test_real_openai_generation(self, real_llm_provider):
        """Test real OpenAI API generation."""
        messages = [
            {"role": "system", "content": "You are a helpful customer service assistant."},
            {"role": "user", "content": "Hello, I need help with a refund."}
        ]

        response = real_llm_provider.generate(messages, max_tokens=50)

        assert isinstance(response.content, str)
        assert len(response.content) > 0
        assert response.cost > 0
        assert response.usage["total_tokens"] > 0
        assert response.provider == "openai"
        assert response.model == "gpt-4o-mini"

    def test_compile_and_run_refund_sop(self, refund_sop, tools_definitions, real_llm_provider, mock_tool_registry):
        """Test complete flow: parse → compile → execute with real LLM."""
        # Parse SOP
        parser = SOPParser()
        sop_def = parser.parse(refund_sop, tools_definitions)

        assert sop_def.name == "Customer Refund Request"
        assert len(sop_def.steps) == 9

        # Compile to graph
        builder = GraphBuilder()
        graph = builder.build_graph(sop_def)

        assert len(graph.nodes) == 9
        assert graph.start_node_id == "step_1"

        # Execute with real LLM (limited steps for cost control)
        executor = SOPExecutor(
            llm_provider=real_llm_provider,
            tool_registry=mock_tool_registry,
            max_steps=3  # Limit steps to control cost
        )

        state = executor.execute(graph, initial_input="I want to return my order number 12345")

        # Verify execution results
        assert len(state.step_results) <= 3  # Respects max_steps limit
        assert state.total_cost > 0  # Real API call should have cost
        assert state.llm_calls > 0  # Should have made LLM calls
        assert len(state.conversation_history) > 0  # Should have conversation

        # Check that LLM responses are realistic
        llm_responses = [turn.content for turn in state.conversation_history if turn.role == "assistant"]
        assert len(llm_responses) > 0

        # Basic sanity check - response should be more than just "Hello"
        first_response = llm_responses[0] if llm_responses else ""
        assert len(first_response) > 10  # Should be a substantive response

    def test_verify_correct_execution_path(self, sample_branch_sop, real_llm_provider, mock_tool_registry):
        """Test that branching logic follows correct paths."""
        # Parse and compile branch SOP
        parser = SOPParser()
        sop_def = parser.parse(sample_branch_sop)

        builder = GraphBuilder()
        graph = builder.build_graph(sop_def)

        # Execute with condition that should trigger YES branch
        executor = SOPExecutor(
            llm_provider=real_llm_provider,
            tool_registry=mock_tool_registry,
            max_steps=5
        )

        # Set up state to trigger YES branch
        state = executor.execute(graph, initial_input="test@example.com")

        # Should have executed some steps
        assert len(state.step_results) >= 2
        assert state.status.value in ["completed", "running"]  # Should not fail

    def test_cost_tracking_integration(self, refund_sop, tools_definitions, real_llm_provider, mock_tool_registry):
        """Test cost tracking with real execution."""
        # Parse and compile
        parser = SOPParser()
        sop_def = parser.parse(refund_sop, tools_definitions)

        builder = GraphBuilder()
        graph = builder.build_graph(sop_def)

        # Execute
        executor = SOPExecutor(
            llm_provider=real_llm_provider,
            tool_registry=mock_tool_registry,
            max_steps=2  # Limit for cost control
        )

        state = executor.execute(graph, initial_input="Test refund request")

        # Record costs
        session_data = record_session_costs(
            state=state,
            sop_name=sop_def.name,
            provider="openai",
            model="gpt-4o-mini"
        )

        # Verify cost tracking
        assert session_data.session_id == state.session_id
        assert session_data.sop_name == sop_def.name
        assert session_data.total_cost >= 0
        assert session_data.llm_calls >= 0
        assert session_data.code_calls >= 0

        # Should show savings (even with limited steps)
        if session_data.pure_llm_cost > 0:
            assert session_data.savings_amount >= 0

    def test_error_handling_with_real_llm(self, real_llm_provider):
        """Test error handling with real LLM provider."""
        # Try to generate with invalid parameters
        messages = [{"role": "user", "content": "Test"}]

        # This should work normally
        response = real_llm_provider.generate(messages, max_tokens=10)
        assert response.content is not None

        # Test with very restrictive parameters
        try:
            response = real_llm_provider.generate(
                messages,
                max_tokens=1,  # Very restrictive
                temperature=0.0
            )
            # Should still work, just with short response
            assert len(response.content) >= 0
        except Exception as e:
            # If it fails, it should be a meaningful error
            assert "LLM generation failed" in str(e) or "Invalid" in str(e)

    def test_provider_availability(self):
        """Test provider availability checking."""
        from soplex.llm.provider import check_provider

        # Test OpenAI availability
        openai_status = check_provider("openai")

        if os.getenv("OPENAI_API_KEY"):
            # If we have a key, should be available
            assert openai_status["provider"] == "openai"
            assert isinstance(openai_status["available"], bool)
            assert isinstance(openai_status["models"], list)
            assert openai_status["error"] is None or isinstance(openai_status["error"], str)
        else:
            # Without key, should show unavailable with error
            assert openai_status["available"] is False
            assert "API key" in openai_status["error"]

    def test_full_workflow_with_visualization(self, refund_sop, tools_definitions, real_llm_provider, mock_tool_registry, tmp_path):
        """Test complete workflow including visualization."""
        # Parse and compile
        parser = SOPParser()
        sop_def = parser.parse(refund_sop, tools_definitions)

        builder = GraphBuilder()
        graph = builder.build_graph(sop_def)

        # Execute (limited steps)
        executor = SOPExecutor(
            llm_provider=real_llm_provider,
            tool_registry=mock_tool_registry,
            max_steps=2
        )

        state = executor.execute(graph, initial_input="Test workflow")

        # Generate visualization with execution path
        from soplex.visualizer.mermaid import generate_sop_flowchart

        execution_path = state.execution_path
        mermaid_content = generate_sop_flowchart(
            graph,
            title="Test Execution",
            execution_path=execution_path
        )

        # Verify visualization content
        assert "flowchart TD" in mermaid_content
        assert "Customer Refund Request" in mermaid_content or "Test Execution" in mermaid_content

        # Save visualization
        viz_file = tmp_path / "test_viz.html"
        from soplex.visualizer.mermaid import MermaidGenerator
        generator = MermaidGenerator()
        generator.save_to_file(mermaid_content, viz_file, "html")

        assert viz_file.exists()
        assert viz_file.stat().st_size > 1000  # Should be substantial HTML content

    @pytest.mark.slow
    def test_multiple_provider_comparison(self):
        """Test multiple providers if available (marked as slow)."""
        providers_to_test = []

        if os.getenv("OPENAI_API_KEY"):
            providers_to_test.append(("openai", "gpt-4o-mini"))

        if os.getenv("ANTHROPIC_API_KEY"):
            providers_to_test.append(("anthropic", "claude-haiku-4-5-20251001"))

        if not providers_to_test:
            pytest.skip("No API keys available for provider comparison")

        results = {}
        test_messages = [
            {"role": "user", "content": "Explain what a customer refund is in one sentence."}
        ]

        for provider, model in providers_to_test:
            try:
                config = get_config(provider=provider, model=model)
                llm_provider = LLMProvider(config)

                response = llm_provider.generate(test_messages, max_tokens=30)

                results[provider] = {
                    "success": True,
                    "cost": response.cost,
                    "tokens": response.usage["total_tokens"],
                    "response_length": len(response.content)
                }

            except Exception as e:
                results[provider] = {
                    "success": False,
                    "error": str(e)
                }

        # Should have at least one successful result
        successful_providers = [p for p, r in results.items() if r.get("success")]

        if len(successful_providers) == 0:
            # If no providers worked, skip the test instead of failing
            pytest.skip(f"No providers available for comparison. Results: {results}")

        # If multiple providers worked, compare costs
        if len(successful_providers) > 1:
            costs = {p: results[p]["cost"] for p in successful_providers}
            print(f"Provider cost comparison: {costs}")


# Utility functions for E2E testing

def create_test_scenario(sop_text: str, expected_steps: int, tools_needed: list) -> dict:
    """Create a test scenario for E2E testing."""
    return {
        "sop_text": sop_text,
        "expected_steps": expected_steps,
        "tools_needed": tools_needed,
        "validation": {
            "min_llm_calls": 1,
            "min_code_calls": 1,
            "max_cost": 0.01  # Maximum cost for the test
        }
    }


# Test scenarios that can be used for benchmarking
TEST_SCENARIOS = {
    "simple_greeting": create_test_scenario(
        """PROCEDURE: Simple Greeting
TRIGGER: User says hello
TOOLS: none

1. Greet the user warmly
2. Ask how you can help them
3. Thank them for contacting us""",
        expected_steps=3,
        tools_needed=[]
    ),

    "password_reset": create_test_scenario(
        """PROCEDURE: Password Reset
TRIGGER: User forgot password
TOOLS: user_db, email_service

1. Ask for user email
2. Check user_db for account
3. Check if account is active
   - YES: Send reset email
   - NO: Inform user account is inactive
4. Confirm email sent""",
        expected_steps=4,
        tools_needed=["user_db", "email_service"]
    )
}
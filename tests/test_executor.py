"""
Tests for executor functionality.
Tests the execution of compiled graphs with mock LLM and tools.
"""
import pytest
from unittest.mock import Mock, patch

from soplex.runtime.executor import SOPExecutor
from soplex.runtime.state import ExecutionState, ExecutionStatus
from soplex.runtime.tool_registry import ToolRegistry
from soplex.compiler.graph import ExecutionGraph, Node, Edge, NodeType
from soplex.llm.provider import LLMProvider, LLMResponse


class TestSOPExecutor:
    """Test SOP execution functionality."""

    @pytest.fixture
    def mock_llm_provider(self):
        """Create mock LLM provider."""
        provider = Mock(spec=LLMProvider)
        provider.generate.return_value = LLMResponse(
            content="Hello! I'll help you with this step.",
            usage={"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
            cost=0.000027,
            model="gpt-4o-mini",
            provider="mock",
            latency_ms=150
        )
        provider.build_system_prompt.return_value = "You are a helpful assistant."
        return provider

    @pytest.fixture
    def mock_tool_registry(self):
        """Create mock tool registry."""
        registry = ToolRegistry()

        # Register mock tools
        def mock_order_lookup(order_number):
            return {
                "order_id": order_number,
                "status": "delivered",
                "total": 99.99,
                "date": "2024-03-01"
            }

        registry.register_tool("order_db", mock_order_lookup, "Order database lookup")
        return registry

    @pytest.fixture
    def simple_linear_graph(self):
        """Create simple linear execution graph."""
        graph = ExecutionGraph(name="Linear Test")

        # Add nodes
        node1 = Node(id="step_1", type=NodeType.LLM, action="Greet user", step_number=1)
        node2 = Node(id="step_2", type=NodeType.CODE, action="Process data", step_number=2,
                    tools_required=["order_db"])
        node3 = Node(id="step_3", type=NodeType.END, action="End", step_number=3)

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        # Add edges
        graph.add_edge(Edge(from_node="step_1", to_node="step_2"))
        graph.add_edge(Edge(from_node="step_2", to_node="step_3"))

        return graph

    @pytest.fixture
    def branch_graph(self):
        """Create graph with branching logic."""
        graph = ExecutionGraph(name="Branch Test")

        node1 = Node(id="step_1", type=NodeType.LLM, action="Ask user", step_number=1)
        node2 = Node(id="branch_2", type=NodeType.BRANCH, action="Check condition",
                    step_number=2, condition="is valid")
        node3 = Node(id="step_3", type=NodeType.LLM, action="Success path", step_number=3)
        node4 = Node(id="step_4", type=NodeType.END, action="Failure path", step_number=4)

        for node in [node1, node2, node3, node4]:
            graph.add_node(node)

        # Add edges
        graph.add_edge(Edge(from_node="step_1", to_node="branch_2"))
        graph.add_edge(Edge(from_node="branch_2", to_node="step_3", condition_type="yes"))
        graph.add_edge(Edge(from_node="branch_2", to_node="step_4", condition_type="no"))

        return graph

    def test_executor_initialization(self, mock_llm_provider, mock_tool_registry):
        """Test executor initialization."""
        executor = SOPExecutor(
            llm_provider=mock_llm_provider,
            tool_registry=mock_tool_registry,
            max_steps=100
        )

        assert executor.llm_provider == mock_llm_provider
        assert executor.tool_registry == mock_tool_registry
        assert executor.max_steps == 100

    def test_execute_linear_graph(self, simple_linear_graph, mock_llm_provider, mock_tool_registry):
        """Test executing simple linear graph."""
        executor = SOPExecutor(
            llm_provider=mock_llm_provider,
            tool_registry=mock_tool_registry
        )

        state = executor.execute(simple_linear_graph, initial_input="Hello")

        # Check execution completed
        assert state.status == ExecutionStatus.COMPLETED
        assert len(state.step_results) == 3
        assert len(state.execution_path) == 3

        # Check step execution order
        assert state.execution_path == ["step_1", "step_2", "step_3"]

        # Check LLM was called
        assert state.llm_calls > 0
        assert state.code_calls > 0
        assert state.total_cost > 0

    def test_execute_yes_branch(self, branch_graph, mock_llm_provider, mock_tool_registry):
        """Test executing YES branch."""
        executor = SOPExecutor(
            llm_provider=mock_llm_provider,
            tool_registry=mock_tool_registry
        )

        # Create state with condition that results in YES
        state = ExecutionState()
        state.data["last_condition_result"] = True

        # Execute
        results = list(executor.execute_interactive(branch_graph, state))

        # Should follow YES path: step_1 -> branch_2 -> step_3
        assert len(results) == 3
        assert results[0].step_id == "step_1"
        assert results[1].step_id == "branch_2"
        assert results[2].step_id == "step_3"

    def test_execute_no_branch(self, branch_graph, mock_llm_provider, mock_tool_registry):
        """Test executing NO branch."""
        executor = SOPExecutor(
            llm_provider=mock_llm_provider,
            tool_registry=mock_tool_registry
        )

        # Create state with condition that results in NO
        state = ExecutionState()
        state.data["last_condition_result"] = False

        # Execute
        results = list(executor.execute_interactive(branch_graph, state))

        # Should follow NO path: step_1 -> branch_2 -> step_4
        assert len(results) == 3
        assert results[0].step_id == "step_1"
        assert results[1].step_id == "branch_2"
        assert results[2].step_id == "step_4"

    def test_escalate_terminates(self, mock_llm_provider, mock_tool_registry):
        """Test that ESCALATE steps terminate execution."""
        graph = ExecutionGraph(name="Escalate Test")

        node1 = Node(id="step_1", type=NodeType.LLM, action="Try to help", step_number=1)
        node2 = Node(id="step_2", type=NodeType.ESCALATE, action="Escalate to human", step_number=2)

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge(Edge(from_node="step_1", to_node="step_2"))

        executor = SOPExecutor(
            llm_provider=mock_llm_provider,
            tool_registry=mock_tool_registry
        )

        state = executor.execute(graph)

        assert state.status == ExecutionStatus.ESCALATED
        assert len(state.step_results) == 2
        assert state.step_results[-1].status == "escalated"

    def test_code_step_skips_llm(self, mock_llm_provider, mock_tool_registry):
        """Test that CODE steps don't call LLM."""
        graph = ExecutionGraph(name="Code Only Test")

        node = Node(id="step_1", type=NodeType.CODE, action="Process data", step_number=1)
        graph.add_node(node)

        executor = SOPExecutor(
            llm_provider=mock_llm_provider,
            tool_registry=mock_tool_registry
        )

        state = executor.execute(graph)

        # CODE step should not have called LLM
        assert mock_llm_provider.generate.call_count == 0
        assert state.llm_calls == 0
        assert state.code_calls > 0

    def test_cost_tracking(self, simple_linear_graph, mock_llm_provider, mock_tool_registry):
        """Test that costs are properly tracked."""
        executor = SOPExecutor(
            llm_provider=mock_llm_provider,
            tool_registry=mock_tool_registry
        )

        state = executor.execute(simple_linear_graph)

        # Should have tracked costs
        assert state.total_cost > 0
        assert state.llm_cost > 0
        assert state.total_tokens > 0

        # Check cost breakdown
        summary = state.get_summary()
        assert "costs" in summary
        assert "usage" in summary
        assert summary["costs"]["total_cost"] > 0

    def test_max_steps_limit(self, mock_llm_provider, mock_tool_registry):
        """Test max steps safety limit."""
        # Create a graph that would loop indefinitely
        graph = ExecutionGraph(name="Loop Test")
        node = Node(id="step_1", type=NodeType.LLM, action="Loop forever", step_number=1)
        graph.add_node(node)
        graph.add_edge(Edge(from_node="step_1", to_node="step_1"))  # Self-loop

        executor = SOPExecutor(
            llm_provider=mock_llm_provider,
            tool_registry=mock_tool_registry,
            max_steps=5  # Low limit for testing
        )

        state = executor.execute(graph)

        # Should stop at max steps
        assert len(state.step_results) <= 5
        assert state.status in [ExecutionStatus.COMPLETED, ExecutionStatus.RUNNING]

    def test_tool_call_integration(self, mock_llm_provider, mock_tool_registry):
        """Test integration with tool calls."""
        graph = ExecutionGraph(name="Tool Test")

        node = Node(
            id="step_1",
            type=NodeType.CODE,
            action="Lookup order details",
            step_number=1,
            tools_required=["order_db"]
        )
        graph.add_node(node)

        executor = SOPExecutor(
            llm_provider=mock_llm_provider,
            tool_registry=mock_tool_registry
        )

        # Set up step parameters
        state = ExecutionState()
        state.step_params = {"order_number": "12345"}

        results = list(executor.execute_interactive(graph, state))

        # Should have called tool and stored result
        assert len(results) == 1
        assert "order_db" in state.tools_used
        assert "order_db_result" in state.data

    def test_hybrid_step_execution(self, mock_llm_provider, mock_tool_registry):
        """Test HYBRID step execution (LLM + code)."""
        graph = ExecutionGraph(name="Hybrid Test")

        node = Node(
            id="step_1",
            type=NodeType.HYBRID,
            action="Ask user and validate response",
            step_number=1
        )
        graph.add_node(node)

        executor = SOPExecutor(
            llm_provider=mock_llm_provider,
            tool_registry=mock_tool_registry
        )

        results = list(executor.execute_interactive(graph))

        assert len(results) == 1
        result = results[0]

        # Should have both LLM and code execution
        assert result.llm_response is not None
        assert result.code_executed
        assert result.cost > 0

    def test_graph_validation(self, mock_llm_provider, mock_tool_registry):
        """Test graph validation before execution."""
        executor = SOPExecutor(
            llm_provider=mock_llm_provider,
            tool_registry=mock_tool_registry
        )

        # Create invalid graph
        graph = ExecutionGraph(name="Invalid Graph")
        node = Node(
            id="step_1",
            type=NodeType.CODE,
            action="Use missing tool",
            step_number=1,
            tools_required=["missing_tool"]
        )
        graph.add_node(node)

        issues = executor.validate_graph(graph)

        assert len(issues) > 0
        assert any("missing_tool" in issue for issue in issues)

    def test_error_handling(self, mock_llm_provider, mock_tool_registry):
        """Test error handling during execution."""
        # Configure mock to raise error
        mock_llm_provider.generate.side_effect = Exception("LLM error")

        graph = ExecutionGraph(name="Error Test")
        node = Node(id="step_1", type=NodeType.LLM, action="This will fail", step_number=1)
        graph.add_node(node)

        executor = SOPExecutor(
            llm_provider=mock_llm_provider,
            tool_registry=mock_tool_registry
        )

        state = executor.execute(graph)

        assert state.status == ExecutionStatus.FAILED
        assert len(state.errors) > 0
        assert state.step_results[0].status == "failed"
        assert "LLM error" in state.step_results[0].error

    def test_interactive_execution(self, simple_linear_graph, mock_llm_provider, mock_tool_registry):
        """Test interactive step-by-step execution."""
        executor = SOPExecutor(
            llm_provider=mock_llm_provider,
            tool_registry=mock_tool_registry
        )

        results = list(executor.execute_interactive(simple_linear_graph))

        # Should yield one result per step
        assert len(results) == 3

        # Each result should have proper structure
        for i, result in enumerate(results):
            assert result.step_id == f"step_{i+1}"
            assert result.step_number == i + 1
            assert result.timestamp is not None
            assert result.duration_ms >= 0
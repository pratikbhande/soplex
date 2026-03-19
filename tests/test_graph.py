"""
Tests for graph engine functionality.
Tests the custom graph implementation and execution graph building.
"""
import pytest
import json
from pathlib import Path
from soplex.compiler.graph import ExecutionGraph, Node, Edge, NodeType
from soplex.compiler.graph_builder import GraphBuilder
from soplex.compiler.code_generator import CodeGenerator


class TestNode:
    """Test Node functionality."""

    def test_create_basic_node(self):
        """Test creating a basic node."""
        node = Node(
            id="test_1",
            type=NodeType.LLM,
            action="Test action",
            step_number=1
        )

        assert node.id == "test_1"
        assert node.type == NodeType.LLM
        assert node.action == "Test action"
        assert node.step_number == 1
        assert node.execution_count == 0

    def test_create_branch_node(self):
        """Test creating a branch node with condition."""
        node = Node(
            id="branch_1",
            type=NodeType.BRANCH,
            action="Check condition",
            step_number=2,
            condition="is active",
            yes_action="proceed",
            no_action="stop"
        )

        assert node.type == NodeType.BRANCH
        assert node.condition == "is active"
        assert node.yes_action == "proceed"
        assert node.no_action == "stop"

    def test_branch_node_validation(self):
        """Test that branch nodes require conditions."""
        with pytest.raises(ValueError, match="BRANCH node .* must have a condition"):
            Node(
                id="invalid_branch",
                type=NodeType.BRANCH,
                action="Check something",
                step_number=1
            )

    def test_node_serialization(self):
        """Test node to_dict and from_dict."""
        node = Node(
            id="test_node",
            type=NodeType.CODE,
            action="Process data",
            step_number=3,
            tools_required=["db", "api"],
            confidence=0.95,
            keywords=["code:process"]
        )

        node_dict = node.to_dict()
        restored_node = Node.from_dict(node_dict)

        assert restored_node.id == node.id
        assert restored_node.type == node.type
        assert restored_node.action == node.action
        assert restored_node.tools_required == node.tools_required
        assert restored_node.confidence == node.confidence


class TestEdge:
    """Test Edge functionality."""

    def test_create_basic_edge(self):
        """Test creating a basic edge."""
        edge = Edge(from_node="node1", to_node="node2")

        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.condition_type == "always"
        assert edge.label == ""

    def test_create_conditional_edge(self):
        """Test creating conditional edges."""
        yes_edge = Edge(from_node="branch1", to_node="node2", condition_type="yes")
        no_edge = Edge(from_node="branch1", to_node="node3", condition_type="no")

        assert yes_edge.condition_type == "yes"
        assert yes_edge.label == "YES"
        assert no_edge.condition_type == "no"
        assert no_edge.label == "NO"

    def test_edge_traversal_always(self):
        """Test edge traversal for always condition."""
        edge = Edge(from_node="node1", to_node="node2", condition_type="always")
        state = {}

        assert edge.should_traverse(state) is True

    def test_edge_traversal_yes(self):
        """Test edge traversal for yes condition."""
        edge = Edge(from_node="branch1", to_node="node2", condition_type="yes")

        # Should traverse when condition is True
        state = {"last_condition_result": True}
        assert edge.should_traverse(state) is True

        # Should not traverse when condition is False
        state = {"last_condition_result": False}
        assert edge.should_traverse(state) is False

    def test_edge_traversal_no(self):
        """Test edge traversal for no condition."""
        edge = Edge(from_node="branch1", to_node="node3", condition_type="no")

        # Should traverse when condition is False
        state = {"last_condition_result": False}
        assert edge.should_traverse(state) is True

        # Should not traverse when condition is True
        state = {"last_condition_result": True}
        assert edge.should_traverse(state) is False

    def test_edge_serialization(self):
        """Test edge serialization."""
        edge = Edge(
            from_node="node1",
            to_node="node2",
            condition_type="yes",
            label="Custom Label"
        )

        edge_dict = edge.to_dict()
        restored_edge = Edge.from_dict(edge_dict)

        assert restored_edge.from_node == edge.from_node
        assert restored_edge.to_node == edge.to_node
        assert restored_edge.condition_type == edge.condition_type
        assert restored_edge.label == edge.label


class TestExecutionGraph:
    """Test ExecutionGraph functionality."""

    def test_create_empty_graph(self):
        """Test creating an empty graph."""
        graph = ExecutionGraph(name="Test Graph")

        assert graph.name == "Test Graph"
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
        assert graph.start_node_id is None

    def test_add_nodes(self):
        """Test adding nodes to graph."""
        graph = ExecutionGraph(name="Test Graph")

        node1 = Node(id="node1", type=NodeType.START, action="Start", step_number=1)
        node2 = Node(id="node2", type=NodeType.LLM, action="Ask user", step_number=2)

        graph.add_node(node1)
        graph.add_node(node2)

        assert len(graph.nodes) == 2
        assert graph.start_node_id == "node1"  # First node becomes start

    def test_add_duplicate_node(self):
        """Test that adding duplicate nodes raises error."""
        graph = ExecutionGraph(name="Test Graph")
        node = Node(id="node1", type=NodeType.LLM, action="Test", step_number=1)

        graph.add_node(node)

        with pytest.raises(ValueError, match="Node node1 already exists"):
            graph.add_node(node)

    def test_add_edges(self):
        """Test adding edges between nodes."""
        graph = ExecutionGraph(name="Test Graph")

        # Add nodes first
        node1 = Node(id="node1", type=NodeType.LLM, action="Start", step_number=1)
        node2 = Node(id="node2", type=NodeType.CODE, action="Process", step_number=2)
        graph.add_node(node1)
        graph.add_node(node2)

        # Add edge
        edge = Edge(from_node="node1", to_node="node2")
        graph.add_edge(edge)

        assert len(graph.edges) == 1

    def test_add_edge_invalid_nodes(self):
        """Test that adding edges with invalid nodes raises error."""
        graph = ExecutionGraph(name="Test Graph")
        edge = Edge(from_node="missing1", to_node="missing2")

        with pytest.raises(ValueError, match="From node missing1 not found"):
            graph.add_edge(edge)

    def test_get_next_nodes_linear(self):
        """Test getting next nodes in linear flow."""
        graph = ExecutionGraph(name="Linear Graph")

        # Create linear flow: node1 -> node2 -> node3
        node1 = Node(id="node1", type=NodeType.LLM, action="Start", step_number=1)
        node2 = Node(id="node2", type=NodeType.CODE, action="Process", step_number=2)
        node3 = Node(id="node3", type=NodeType.END, action="End", step_number=3)

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        edge1 = Edge(from_node="node1", to_node="node2")
        edge2 = Edge(from_node="node2", to_node="node3")
        graph.add_edge(edge1)
        graph.add_edge(edge2)

        # Test navigation
        state = {}
        next_nodes = graph.get_next_nodes("node1", state)
        assert next_nodes == ["node2"]

        next_node = graph.get_next("node1", state)
        assert next_node == "node2"

        # Test end node
        next_node = graph.get_next("node3", state)
        assert next_node is None

    def test_get_next_nodes_branch(self):
        """Test getting next nodes with branching."""
        graph = ExecutionGraph(name="Branch Graph")

        # Create branch flow: node1 -> branch2 -> (node3 | node4)
        node1 = Node(id="node1", type=NodeType.LLM, action="Ask", step_number=1)
        branch2 = Node(id="branch2", type=NodeType.BRANCH, action="Check condition",
                      step_number=2, condition="is valid")
        node3 = Node(id="node3", type=NodeType.LLM, action="Success path", step_number=3)
        node4 = Node(id="node4", type=NodeType.LLM, action="Failure path", step_number=4)

        for node in [node1, branch2, node3, node4]:
            graph.add_node(node)

        # Add edges
        graph.add_edge(Edge(from_node="node1", to_node="branch2"))
        graph.add_edge(Edge(from_node="branch2", to_node="node3", condition_type="yes"))
        graph.add_edge(Edge(from_node="branch2", to_node="node4", condition_type="no"))

        # Test YES condition
        state = {"last_condition_result": True}
        next_nodes = graph.get_next_nodes("branch2", state)
        assert next_nodes == ["node3"]

        # Test NO condition
        state = {"last_condition_result": False}
        next_nodes = graph.get_next_nodes("branch2", state)
        assert next_nodes == ["node4"]

    def test_graph_validation(self):
        """Test graph validation."""
        graph = ExecutionGraph(name="Test Graph")

        # Empty graph should have issues
        issues = graph.validate()
        assert "No valid start node" in issues[0]

        # Add nodes but leave one orphaned
        node1 = Node(id="node1", type=NodeType.LLM, action="Start", step_number=1)
        node2 = Node(id="node2", type=NodeType.CODE, action="Connected", step_number=2)
        node3 = Node(id="node3", type=NodeType.LLM, action="Orphaned", step_number=3)

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        # Connect only node1 -> node2, leaving node3 orphaned
        graph.add_edge(Edge(from_node="node1", to_node="node2"))

        issues = graph.validate()
        assert any("Orphaned nodes" in issue for issue in issues)

    def test_graph_summary(self):
        """Test graph summary generation."""
        graph = ExecutionGraph(name="Summary Test", tools_required=["tool1", "tool2"])

        node1 = Node(id="node1", type=NodeType.LLM, action="Start", step_number=1)
        node2 = Node(id="node2", type=NodeType.CODE, action="Process", step_number=2)
        node3 = Node(id="branch3", type=NodeType.BRANCH, action="Check",
                    step_number=3, condition="test")

        for node in [node1, node2, node3]:
            graph.add_node(node)

        summary = graph.summary()

        assert summary["name"] == "Summary Test"
        assert summary["total_nodes"] == 3
        assert summary["total_edges"] == 0
        assert summary["node_types"]["llm"] == 1
        assert summary["node_types"]["code"] == 1
        assert summary["node_types"]["branch"] == 1
        assert summary["tools_required"] == ["tool1", "tool2"]

    def test_mermaid_generation(self):
        """Test Mermaid diagram generation."""
        graph = ExecutionGraph(name="Mermaid Test")

        node1 = Node(id="node1", type=NodeType.START, action="Start process", step_number=1)
        node2 = Node(id="node2", type=NodeType.LLM, action="Ask user for input", step_number=2)
        node3 = Node(id="node3", type=NodeType.END, action="End process", step_number=3)

        for node in [node1, node2, node3]:
            graph.add_node(node)

        graph.add_edge(Edge(from_node="node1", to_node="node2"))
        graph.add_edge(Edge(from_node="node2", to_node="node3"))

        mermaid = graph.to_mermaid()

        assert "flowchart TD" in mermaid
        assert "node1" in mermaid
        assert "node2" in mermaid
        assert "node3" in mermaid
        assert "1. Start process" in mermaid
        assert "2. Ask user for input" in mermaid
        assert "3. End process" in mermaid
        assert "-->" in mermaid

    def test_graph_save_load(self, tmp_path):
        """Test saving and loading graphs."""
        # Create test graph
        graph = ExecutionGraph(name="Save Test", tools_required=["tool1"])

        node1 = Node(id="node1", type=NodeType.LLM, action="Test action", step_number=1)
        node2 = Node(id="node2", type=NodeType.CODE, action="Process", step_number=2,
                    handler_code="def test(): pass")

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge(Edge(from_node="node1", to_node="node2"))

        # Save graph
        save_path = tmp_path / "test_graph.json"
        graph.save(save_path)

        assert save_path.exists()

        # Load graph
        loaded_graph = ExecutionGraph.load(save_path)

        assert loaded_graph.name == graph.name
        assert loaded_graph.tools_required == graph.tools_required
        assert len(loaded_graph.nodes) == len(graph.nodes)
        assert len(loaded_graph.edges) == len(graph.edges)

        # Verify node details
        loaded_node2 = loaded_graph.get_node("node2")
        assert loaded_node2.handler_code == "def test(): pass"


class TestGraphBuilder:
    """Test GraphBuilder functionality."""

    def test_build_simple_graph(self, parsed_linear_sop):
        """Test building graph from simple linear SOP."""
        builder = GraphBuilder()
        graph = builder.build_graph(parsed_linear_sop)

        assert graph.name == "Simple Greeting"
        assert len(graph.nodes) == 3
        assert len(graph.edges) == 2  # Linear connections

        # Verify node types
        nodes_by_type = {}
        for node in graph.nodes.values():
            nodes_by_type[node.type] = nodes_by_type.get(node.type, 0) + 1

        assert NodeType.LLM in nodes_by_type

    def test_build_branch_graph(self, parsed_branch_sop):
        """Test building graph with branching logic."""
        builder = GraphBuilder()
        graph = builder.build_graph(parsed_branch_sop)

        assert graph.name == "Account Verification"
        assert len(graph.nodes) >= 4

        # Find branch nodes
        branch_nodes = [n for n in graph.nodes.values() if n.type == NodeType.BRANCH]
        assert len(branch_nodes) >= 1

        # Verify branch has conditional edges
        branch_node = branch_nodes[0]
        outgoing_edges = graph.get_outgoing_edges(branch_node.id)

        # Should have YES and NO edges
        edge_types = [e.condition_type for e in outgoing_edges]
        assert "yes" in edge_types or "no" in edge_types

    def test_code_generation(self, parsed_linear_sop):
        """Test that code is generated for appropriate steps."""
        builder = GraphBuilder()
        graph = builder.build_graph(parsed_linear_sop)

        # Check for generated code in CODE/BRANCH nodes
        code_nodes = [n for n in graph.nodes.values()
                     if n.type in [NodeType.CODE, NodeType.BRANCH, NodeType.HYBRID]]

        for node in code_nodes:
            # These nodes should have generated handler code
            assert node.handler_code is not None
            assert "def handle_" in node.handler_code

    def test_graph_complexity_analysis(self, parsed_refund_sop):
        """Test complexity analysis of built graphs."""
        builder = GraphBuilder()
        graph = builder.build_graph(parsed_refund_sop)

        analysis = builder.analyze_graph_complexity(graph)

        assert "total_nodes" in analysis
        assert "branch_points" in analysis
        assert "complexity_score" in analysis
        assert "complexity_level" in analysis
        assert analysis["complexity_level"] in ["simple", "moderate", "complex"]


class TestCodeGenerator:
    """Test code generation functionality."""

    def test_generate_code_handler(self):
        """Test generating handler for CODE step."""
        from soplex.parser.models import Step, StepType

        step = Step(
            id="step_1",
            number=1,
            text="1. Process the payment using payment_api",
            type=StepType.CODE,
            action="Process the payment using payment_api",
            tools_required=["payment_api"]
        )

        generator = CodeGenerator()
        handler_code = generator.generate_step_handler(step)

        assert handler_code != ""
        assert "def handle_step_1" in handler_code
        assert "payment_api" in handler_code
        assert "tools.get" in handler_code

    def test_generate_branch_handler(self):
        """Test generating handler for BRANCH step."""
        from soplex.parser.models import Step, StepType, BranchCondition

        branch = BranchCondition(
            condition="Check if order was placed within 30 days",
            yes_action="Proceed to refund",
            no_action="Inform customer about policy"
        )

        step = Step(
            id="step_2",
            number=2,
            text="2. Check if order within 30 days",
            type=StepType.BRANCH,
            action="Check if order was placed within 30 days",
            branch=branch
        )

        generator = CodeGenerator()
        handler_code = generator.generate_step_handler(step)

        assert handler_code != ""
        assert "def handle_step_2" in handler_code
        assert "30" in handler_code  # Should extract the number of days
        assert "timedelta" in handler_code  # Should use datetime

    def test_compile_handlers_module(self):
        """Test compiling all handlers into a module."""
        generator = CodeGenerator()

        handlers = {
            "step_1": "def handle_step_1(): pass",
            "step_2": "def handle_step_2(): pass",
        }

        module_code = generator.compile_handlers_module(handlers)

        assert "Generated handlers for soplex" in module_code
        assert "handle_step_1" in module_code
        assert "handle_step_2" in module_code
        assert "STEP_HANDLERS = {" in module_code
        assert '"step_1": handle_step_1,' in module_code
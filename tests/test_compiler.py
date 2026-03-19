"""
Tests for compiler functionality.
Tests the integration between parser and graph building.
"""
import pytest
from soplex.parser.sop_parser import SOPParser
from soplex.compiler.graph_builder import GraphBuilder
from soplex.compiler.graph import NodeType


class TestCompiler:
    """Test compiler integration functionality."""

    def test_compile_refund_sop(self, refund_sop, tools_definitions):
        """Test compiling the refund example SOP."""
        # Parse SOP
        parser = SOPParser()
        sop_def = parser.parse(refund_sop, tools_definitions)

        # Build graph
        builder = GraphBuilder()
        graph = builder.build_graph(sop_def)

        # Verify graph structure
        assert graph.name == "Customer Refund Request"
        assert len(graph.nodes) == 9  # 9 steps in refund SOP
        assert graph.start_node_id == "step_1"

        # Verify tools are preserved
        assert "order_db" in graph.tools_required
        assert "payments_api" in graph.tools_required
        assert "identity_check" in graph.tools_required

        # Verify compilation timestamp exists
        assert graph.compilation_timestamp is not None

    def test_correct_node_count(self, refund_sop, tools_definitions):
        """Test that all steps are converted to nodes."""
        parser = SOPParser()
        sop_def = parser.parse(refund_sop, tools_definitions)

        builder = GraphBuilder()
        graph = builder.build_graph(sop_def)

        # Should have same number of nodes as steps
        assert len(graph.nodes) == len(sop_def.steps)

        # Each step should have corresponding node
        for step in sop_def.steps:
            node = graph.get_node(step.id)
            assert node is not None
            assert node.step_number == step.number
            assert node.action == step.action

    def test_code_handlers_exist(self, refund_sop, tools_definitions):
        """Test that CODE/BRANCH steps have generated handlers."""
        parser = SOPParser()
        sop_def = parser.parse(refund_sop, tools_definitions)

        builder = GraphBuilder()
        graph = builder.build_graph(sop_def)

        # Find CODE and BRANCH nodes
        code_nodes = [n for n in graph.nodes.values()
                     if n.type in [NodeType.CODE, NodeType.BRANCH, NodeType.HYBRID]]

        assert len(code_nodes) > 0  # Should have some CODE/BRANCH nodes

        # These nodes should have handler code
        for node in code_nodes:
            assert node.handler_code is not None
            assert "def handle_" in node.handler_code
            assert node.id in node.handler_code

    def test_branch_edges_correct(self, sample_branch_sop):
        """Test that branch steps have correct YES/NO edges."""
        parser = SOPParser()
        sop_def = parser.parse(sample_branch_sop)

        builder = GraphBuilder()
        graph = builder.build_graph(sop_def)

        # Find branch nodes
        branch_nodes = [n for n in graph.nodes.values() if n.type == NodeType.BRANCH]
        assert len(branch_nodes) > 0

        for branch_node in branch_nodes:
            # Get outgoing edges
            edges = graph.get_outgoing_edges(branch_node.id)

            # Should have at least one conditional edge
            conditional_edges = [e for e in edges if e.condition_type in ["yes", "no"]]
            assert len(conditional_edges) > 0

    def test_start_node_set(self, parsed_linear_sop):
        """Test that start node is correctly set."""
        builder = GraphBuilder()
        graph = builder.build_graph(parsed_linear_sop)

        assert graph.start_node_id is not None
        start_node = graph.get_node(graph.start_node_id)
        assert start_node is not None
        assert start_node.step_number == 1  # Should be first step

    def test_linear_graph_creation(self, parsed_linear_sop):
        """Test creating linear graph (fallback mode)."""
        builder = GraphBuilder()
        linear_graph = builder.create_linear_graph(parsed_linear_sop)

        assert "Linear" in linear_graph.name
        assert len(linear_graph.nodes) == len(parsed_linear_sop.steps)

        # Should have linear edges (n-1 edges for n nodes)
        expected_edges = len(parsed_linear_sop.steps) - 1
        assert len(linear_graph.edges) == expected_edges

    def test_complexity_analysis(self, refund_sop, tools_definitions):
        """Test graph complexity analysis."""
        parser = SOPParser()
        sop_def = parser.parse(refund_sop, tools_definitions)

        builder = GraphBuilder()
        graph = builder.build_graph(sop_def)

        analysis = builder.analyze_graph_complexity(graph)

        # Verify analysis structure
        required_keys = [
            "total_nodes", "total_edges", "branch_points",
            "terminal_nodes", "complexity_score", "complexity_level"
        ]

        for key in required_keys:
            assert key in analysis

        # Verify reasonable values
        assert analysis["total_nodes"] > 0
        assert analysis["complexity_level"] in ["simple", "moderate", "complex"]
        assert analysis["complexity_score"] >= 0
"""
Native Python Graph Builder API for Soplex.
Allows developers to build ExecutionGraph objects programmatically,
bypassing the text-based SOP parser and injecting native Python callables.
"""
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from .graph import ExecutionGraph, Node, Edge, NodeType


class PythonGraphBuilder:
    """
    A builder for constructing Soplex ExecutionGraphs using a native Python API.
    This bypasses the plain-text SOP parser, allowing developers to define
    execution nodes, edge connections, and native Python `handler` functions explicitly.
    """

    def __init__(self, name: str, tools_required: Optional[List[str]] = None):
        """
        Initialize a new Python Graph Builder.

        Args:
            name: Name of the SOP graph.
            tools_required: Optional list of required tools for this graph.
        """
        self.graph = ExecutionGraph(
            name=name,
            sop_source="Python API",
            compilation_timestamp=datetime.now().isoformat(),
            tools_required=tools_required or [],
        )
        self._step_counter = 1

    def _create_node(
        self,
        node_id: str,
        node_type: NodeType,
        action: str,
        handler: Optional[Callable] = None,
        tools_required: Optional[List[str]] = None,
        condition: Optional[str] = None,
        yes_action: Optional[str] = None,
        no_action: Optional[str] = None,
    ) -> Node:
        """Internal helper to create and add a node."""
        node = Node(
            id=node_id,
            type=node_type,
            action=action,
            step_number=self._step_counter,
            handler=handler,
            tools_required=tools_required or [],
            condition=condition,
            yes_action=yes_action,
            no_action=no_action,
        )
        self.graph.add_node(node)
        self._step_counter += 1
        return node

    def add_llm_step(self, id: str, action: str, tools_required: Optional[List[str]] = None):
        """
        Add a conversational LLM step.

        Args:
            id: Unique identifier for the step (e.g., 'greet_user')
            action: Prompt instructions or description of the action.
            tools_required: List of tool names this step can invoke.
        """
        self._create_node(
            node_id=id,
            node_type=NodeType.LLM,
            action=action,
            tools_required=tools_required,
        )

    def add_code_step(
        self, 
        id: str, 
        action: str, 
        handler_func: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        tools_required: Optional[List[str]] = None
    ):
        """
        Add a deterministic code step.

        Args:
            id: Unique identifier for the step.
            action: Description of the action (used for logging/tracing).
            handler_func: A native Python callable that takes the execution state (dict) and returns the updated state dict.
            tools_required: List of accessible tools.
        """
        self._create_node(
            node_id=id,
            node_type=NodeType.CODE,
            action=action,
            handler=handler_func,
            tools_required=tools_required,
        )

    def add_branch_step(
        self,
        id: str,
        action: str,
    ):
        """
        Add a conditional branching step base node.
        Edges should be added explicitly afterwards using `add_edge(...)`.

        Args:
            id: Unique identifier for the step.
            action: Description of what is being checked.
        """
        # Node itself acts as the branch point
        self._create_node(
            node_id=id,
            node_type=NodeType.BRANCH,
            action=action,
            condition=action,  # Set condition string for graph visualization
        )

    def add_end_step(self, id: str, action: str = "Complete the process"):
        """Add a terminal/end step to the graph."""
        self._create_node(
            node_id=id,
            node_type=NodeType.END,
            action=action,
        )

    def add_edge(
        self,
        from_node: str,
        to_node: str,
        condition_func: Optional[Callable[[Dict[str, Any]], bool]] = None,
        label: Optional[str] = None,
    ):
        """
        Add a directional edge between two nodes.

        Args:
            from_node: ID of the originating node.
            to_node: ID of the destination node.
            condition_func: Optional Python callable that takes the state and returns True if this edge should be traversed.
            label: Visual label for the edge diagram.
        """
        if condition_func:
            edge = Edge(
                from_node=from_node,
                to_node=to_node,
                condition=condition_func,
                condition_type="custom",
                label=label,
            )
        else:
            edge = Edge(
                from_node=from_node,
                to_node=to_node,
                condition_type="always",
                label=label,
            )
        self.graph.add_edge(edge)

    def build(self) -> ExecutionGraph:
        """
        Validate and return the constructed ExecutionGraph.

        Returns:
            The fully constructed ExecutionGraph ready for execution.
            
        Raises:
            ValueError: If the graph structure is invalid (e.g. missing links).
        """
        issues = self.graph.validate()
        if issues:
            raise ValueError(f"Graph validation failed: {issues}")
        return self.graph

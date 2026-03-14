"""
Custom lightweight graph engine for soplex.
Provides Node, Edge, and ExecutionGraph classes for representing SOP execution flows.
Zero external dependencies - pure Python dataclasses.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union
import json
from pathlib import Path
from enum import Enum


class NodeType(str, Enum):
    """Types of nodes in the execution graph."""
    START = "start"
    LLM = "llm"
    CODE = "code"
    HYBRID = "hybrid"
    BRANCH = "branch"
    END = "end"
    ESCALATE = "escalate"


@dataclass
class Node:
    """
    Represents a single node in the execution graph.
    """
    id: str
    type: NodeType
    action: str
    step_number: int

    # Execution handlers
    handler: Optional[Callable] = field(default=None, repr=False)
    handler_code: Optional[str] = None

    # Node metadata
    tools_required: List[str] = field(default_factory=list)
    confidence: float = 1.0
    keywords: List[str] = field(default_factory=list)

    # Branch-specific data
    condition: Optional[str] = None
    yes_action: Optional[str] = None
    no_action: Optional[str] = None

    # Runtime data
    execution_count: int = field(default=0, init=False)
    total_latency_ms: float = field(default=0.0, init=False)

    def __post_init__(self):
        """Validate node data after initialization."""
        if self.type == NodeType.BRANCH and not self.condition:
            raise ValueError(f"BRANCH node {self.id} must have a condition")

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "action": self.action,
            "step_number": self.step_number,
            "handler_code": self.handler_code,
            "tools_required": self.tools_required,
            "confidence": self.confidence,
            "keywords": self.keywords,
            "condition": self.condition,
            "yes_action": self.yes_action,
            "no_action": self.no_action,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        """Create node from dictionary."""
        return cls(
            id=data["id"],
            type=NodeType(data["type"]),
            action=data["action"],
            step_number=data["step_number"],
            handler_code=data.get("handler_code"),
            tools_required=data.get("tools_required", []),
            confidence=data.get("confidence", 1.0),
            keywords=data.get("keywords", []),
            condition=data.get("condition"),
            yes_action=data.get("yes_action"),
            no_action=data.get("no_action"),
        )


@dataclass
class Edge:
    """
    Represents a directed edge between nodes.
    """
    from_node: str
    to_node: str
    condition: Optional[Callable] = field(default=None, repr=False)
    condition_type: str = "always"  # "always", "yes", "no", "custom"
    label: Optional[str] = None

    def __post_init__(self):
        """Set default label if not provided."""
        if not self.label:
            if self.condition_type == "always":
                self.label = ""
            elif self.condition_type in ["yes", "no"]:
                self.label = self.condition_type.upper()
            else:
                self.label = "condition"

    def should_traverse(self, state: Dict[str, Any]) -> bool:
        """
        Determine if this edge should be traversed given the current state.

        Args:
            state: Current execution state

        Returns:
            True if edge should be traversed
        """
        if self.condition_type == "always":
            return True
        elif self.condition_type == "yes":
            return state.get("last_condition_result", False)
        elif self.condition_type == "no":
            return not state.get("last_condition_result", False)
        elif self.condition and callable(self.condition):
            return self.condition(state)
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary for serialization."""
        return {
            "from_node": self.from_node,
            "to_node": self.to_node,
            "condition_type": self.condition_type,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Edge":
        """Create edge from dictionary."""
        return cls(
            from_node=data["from_node"],
            to_node=data["to_node"],
            condition_type=data.get("condition_type", "always"),
            label=data.get("label"),
        )


@dataclass
class ExecutionGraph:
    """
    Represents the complete execution graph for a compiled SOP.
    """
    name: str
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    start_node_id: Optional[str] = None

    # Graph metadata
    sop_source: str = ""
    compilation_timestamp: Optional[str] = None
    tools_required: List[str] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        if node.id in self.nodes:
            raise ValueError(f"Node {node.id} already exists in graph")
        self.nodes[node.id] = node

        # Set start node if this is the first node
        if not self.start_node_id:
            self.start_node_id = node.id

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph."""
        if edge.from_node not in self.nodes:
            raise ValueError(f"From node {edge.from_node} not found in graph")
        if edge.to_node not in self.nodes:
            raise ValueError(f"To node {edge.to_node} not found in graph")
        self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_outgoing_edges(self, node_id: str) -> List[Edge]:
        """Get all edges originating from a node."""
        return [edge for edge in self.edges if edge.from_node == node_id]

    def get_incoming_edges(self, node_id: str) -> List[Edge]:
        """Get all edges targeting a node."""
        return [edge for edge in self.edges if edge.to_node == node_id]

    def get_next_nodes(self, current_node_id: str, state: Dict[str, Any]) -> List[str]:
        """
        Get the next node IDs based on current state and edge conditions.

        Args:
            current_node_id: ID of current node
            state: Current execution state

        Returns:
            List of next node IDs to execute
        """
        next_nodes = []
        outgoing_edges = self.get_outgoing_edges(current_node_id)

        for edge in outgoing_edges:
            if edge.should_traverse(state):
                next_nodes.append(edge.to_node)

        return next_nodes

    def get_next(self, current_node_id: str, state: Dict[str, Any]) -> Optional[str]:
        """
        Get the single next node ID (for linear execution).

        Args:
            current_node_id: ID of current node
            state: Current execution state

        Returns:
            Next node ID or None if end of execution
        """
        next_nodes = self.get_next_nodes(current_node_id, state)
        return next_nodes[0] if next_nodes else None

    def validate(self) -> List[str]:
        """
        Validate the graph structure and return any issues.

        Returns:
            List of validation error messages
        """
        issues = []

        # Check for start node
        if not self.start_node_id or self.start_node_id not in self.nodes:
            issues.append("No valid start node specified")

        # Check for orphaned nodes (no incoming edges except start)
        nodes_with_incoming = {edge.to_node for edge in self.edges}
        nodes_with_incoming.add(self.start_node_id)  # Start node is okay without incoming

        orphaned = set(self.nodes.keys()) - nodes_with_incoming
        if orphaned:
            issues.append(f"Orphaned nodes: {', '.join(orphaned)}")

        # Check for nodes with no outgoing edges (should be END or ESCALATE)
        for node_id, node in self.nodes.items():
            outgoing = self.get_outgoing_edges(node_id)
            if not outgoing and node.type not in [NodeType.END, NodeType.ESCALATE]:
                issues.append(f"Node {node_id} has no outgoing edges but is not terminal")

        # Check for invalid edge references
        all_node_ids = set(self.nodes.keys())
        for edge in self.edges:
            if edge.from_node not in all_node_ids:
                issues.append(f"Edge references missing from_node: {edge.from_node}")
            if edge.to_node not in all_node_ids:
                issues.append(f"Edge references missing to_node: {edge.to_node}")

        return issues

    def summary(self) -> Dict[str, Any]:
        """Get summary statistics for the graph."""
        node_types = {}
        for node in self.nodes.values():
            node_types[node.type.value] = node_types.get(node.type.value, 0) + 1

        return {
            "name": self.name,
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": node_types,
            "start_node": self.start_node_id,
            "tools_required": self.tools_required,
        }

    def to_mermaid(self) -> str:
        """
        Generate Mermaid flowchart representation of the graph.

        Returns:
            Mermaid flowchart syntax
        """
        lines = ["flowchart TD"]

        # Define node styles based on type
        style_map = {
            NodeType.START: "fill:#e1f5fe,stroke:#01579b",
            NodeType.LLM: "fill:#cce5ff,stroke:#1976d2",
            NodeType.CODE: "fill:#d4edda,stroke:#155724",
            NodeType.HYBRID: "fill:#fff3cd,stroke:#856404",
            NodeType.BRANCH: "fill:#d4edda,stroke:#155724",
            NodeType.END: "fill:#e2e3e5,stroke:#6c757d",
            NodeType.ESCALATE: "fill:#f8d7da,stroke:#721c24",
        }

        # Add nodes
        for node in self.nodes.values():
            # Create node label (truncate long actions)
            action = node.action[:30] + "..." if len(node.action) > 33 else node.action
            label = f"{node.step_number}. {action}"

            # Node shape based on type
            if node.type == NodeType.BRANCH:
                lines.append(f'    {node.id}{{"{label}"}}')
            elif node.type in [NodeType.END, NodeType.ESCALATE]:
                lines.append(f'    {node.id}["{label}"]')
            else:
                lines.append(f'    {node.id}["{label}"]')

        # Add edges
        for edge in self.edges:
            if edge.label:
                lines.append(f"    {edge.from_node} -->|{edge.label}| {edge.to_node}")
            else:
                lines.append(f"    {edge.from_node} --> {edge.to_node}")

        # Add styles
        for node_id, node in self.nodes.items():
            style = style_map.get(node.type, "fill:#f9f9f9,stroke:#333")
            lines.append(f"    style {node_id} {style}")

        return "\n".join(lines)

    def save(self, file_path: Union[str, Path]) -> None:
        """
        Save graph to JSON file.

        Args:
            file_path: Path to save the graph
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        graph_data = {
            "name": self.name,
            "start_node_id": self.start_node_id,
            "sop_source": self.sop_source,
            "compilation_timestamp": self.compilation_timestamp,
            "tools_required": self.tools_required,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges],
        }

        with open(path, "w") as f:
            json.dump(graph_data, f, indent=2)

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "ExecutionGraph":
        """
        Load graph from JSON file.

        Args:
            file_path: Path to the graph file

        Returns:
            Loaded ExecutionGraph instance
        """
        with open(file_path) as f:
            graph_data = json.load(f)

        graph = cls(
            name=graph_data["name"],
            start_node_id=graph_data.get("start_node_id"),
            sop_source=graph_data.get("sop_source", ""),
            compilation_timestamp=graph_data.get("compilation_timestamp"),
            tools_required=graph_data.get("tools_required", []),
        )

        # Load nodes
        for node_data in graph_data["nodes"]:
            node = Node.from_dict(node_data)
            graph.nodes[node.id] = node

        # Load edges
        for edge_data in graph_data["edges"]:
            edge = Edge.from_dict(edge_data)
            graph.edges.append(edge)

        return graph

    def visualize_path(self, execution_path: List[str]) -> str:
        """
        Generate Mermaid diagram highlighting an execution path.

        Args:
            execution_path: List of node IDs representing execution path

        Returns:
            Mermaid flowchart with highlighted path
        """
        base_mermaid = self.to_mermaid()

        # Add path highlighting
        for i, node_id in enumerate(execution_path):
            base_mermaid += f"\n    style {node_id} fill:#ffeb3b,stroke:#f57f17"
            if i > 0:
                # Highlight the edge too
                prev_node = execution_path[i-1]
                base_mermaid += f"\n    linkStyle {i-1} stroke:#f57f17,stroke-width:3px"

        return base_mermaid
"""
Mermaid flowchart generator for soplex.
Creates visual flowcharts from execution graphs.
"""
from typing import Dict, List, Optional, Any
from pathlib import Path
from ..compiler.graph import ExecutionGraph, NodeType
from ..config import VISUALIZATION_COLORS


class MermaidGenerator:
    """
    Generates Mermaid flowchart diagrams from execution graphs.
    """

    def __init__(self, custom_colors: Optional[Dict[str, str]] = None):
        """Initialize generator with optional custom colors."""
        self.colors = custom_colors or VISUALIZATION_COLORS.copy()

    def generate_flowchart(
        self,
        graph: ExecutionGraph,
        title: Optional[str] = None,
        show_step_numbers: bool = True,
        max_action_length: int = 40,
        highlight_path: Optional[List[str]] = None
    ) -> str:
        """
        Generate Mermaid flowchart from execution graph.

        Args:
            graph: Execution graph to visualize
            title: Optional title for the diagram
            show_step_numbers: Include step numbers in node labels
            max_action_length: Maximum length of action text
            highlight_path: List of node IDs to highlight (execution path)

        Returns:
            Mermaid flowchart string
        """
        lines = []

        # Add title if provided
        if title:
            lines.extend([
                "---",
                f"title: {title}",
                "---",
                ""
            ])

        # Start flowchart
        lines.append("flowchart TD")
        lines.append("")

        # Generate node definitions
        node_lines = self._generate_nodes(graph, show_step_numbers, max_action_length)
        lines.extend(node_lines)

        lines.append("")

        # Generate edge definitions
        edge_lines = self._generate_edges(graph)
        lines.extend(edge_lines)

        lines.append("")

        # Generate style definitions
        style_lines = self._generate_styles(graph, highlight_path)
        lines.extend(style_lines)

        return "\n".join(lines)

    def generate_with_execution_path(
        self,
        graph: ExecutionGraph,
        execution_path: List[str],
        title: Optional[str] = None
    ) -> str:
        """
        Generate flowchart highlighting an execution path.

        Args:
            graph: Execution graph
            execution_path: List of node IDs that were executed
            title: Optional title

        Returns:
            Mermaid flowchart with highlighted path
        """
        return self.generate_flowchart(
            graph,
            title=title or f"{graph.name} - Execution Path",
            highlight_path=execution_path
        )

    def generate_comparison(
        self,
        original_graph: ExecutionGraph,
        optimized_graph: ExecutionGraph,
        title: str = "Graph Comparison"
    ) -> str:
        """
        Generate side-by-side comparison of two graphs.

        Args:
            original_graph: Original graph
            optimized_graph: Optimized graph
            title: Title for the comparison

        Returns:
            Mermaid diagram showing both graphs
        """
        lines = [
            "---",
            f"title: {title}",
            "---",
            "",
            "flowchart TD",
            "    subgraph Original[\"Original SOP\"]",
            "        direction TD",
        ]

        # Generate original graph nodes (with prefix "o_")
        for node in original_graph.nodes.values():
            action = self._truncate_action(node.action, 30)
            label = f"{node.step_number}. {action}" if node.step_number else action
            node_id = f"o_{node.id}"
            lines.append(f"        {node_id}[{label}]")

        lines.extend([
            "    end",
            "",
            "    subgraph Optimized[\"Optimized SOP\"]",
            "        direction TD",
        ])

        # Generate optimized graph nodes (with prefix "n_")
        for node in optimized_graph.nodes.values():
            action = self._truncate_action(node.action, 30)
            label = f"{node.step_number}. {action}" if node.step_number else action
            node_id = f"n_{node.id}"
            lines.append(f"        {node_id}[{label}]")

        lines.append("    end")

        # Add edges for original graph
        lines.append("")
        lines.append("    %% Original graph edges")
        for edge in original_graph.edges:
            from_id = f"o_{edge.from_node}"
            to_id = f"o_{edge.to_node}"
            if edge.label:
                lines.append(f"    {from_id} -->|{edge.label}| {to_id}")
            else:
                lines.append(f"    {from_id} --> {to_id}")

        # Add edges for optimized graph
        lines.append("")
        lines.append("    %% Optimized graph edges")
        for edge in optimized_graph.edges:
            from_id = f"n_{edge.from_node}"
            to_id = f"n_{edge.to_node}"
            if edge.label:
                lines.append(f"    {from_id} -->|{edge.label}| {to_id}")
            else:
                lines.append(f"    {from_id} --> {to_id}")

        return "\n".join(lines)

    def save_to_file(
        self,
        mermaid_content: str,
        output_path: Path,
        format: str = "mmd"
    ) -> None:
        """
        Save Mermaid content to file.

        Args:
            mermaid_content: Generated Mermaid content
            output_path: Output file path
            format: Output format ("mmd" for Mermaid, "html" for HTML wrapper)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "mmd":
            with open(output_path, 'w') as f:
                f.write(mermaid_content)

        elif format.lower() == "html":
            html_content = self._wrap_in_html(mermaid_content)
            with open(output_path, 'w') as f:
                f.write(html_content)

        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_nodes(
        self,
        graph: ExecutionGraph,
        show_step_numbers: bool,
        max_action_length: int
    ) -> List[str]:
        """Generate node definitions."""
        lines = ["    %% Node definitions"]

        for node in graph.nodes.values():
            # Create node label
            action = self._truncate_action(node.action, max_action_length)
            if show_step_numbers and node.step_number:
                label = f"{node.step_number}. {action}"
            else:
                label = action

            # Escape quotes and special characters
            label = label.replace('"', '\\"').replace('\n', ' ')

            # Choose node shape based on type
            if node.type == NodeType.BRANCH:
                lines.append(f'    {node.id}{{"{label}"}}')
            elif node.type in [NodeType.END, NodeType.ESCALATE]:
                lines.append(f'    {node.id}(["{label}"])')
            elif node.type == NodeType.CODE:
                lines.append(f'    {node.id}["{label}"]')
            else:  # LLM, HYBRID, START
                lines.append(f'    {node.id}["{label}"]')

        return lines

    def _generate_edges(self, graph: ExecutionGraph) -> List[str]:
        """Generate edge definitions."""
        lines = ["    %% Edge definitions"]

        for edge in graph.edges:
            if edge.label:
                lines.append(f"    {edge.from_node} -->|{edge.label}| {edge.to_node}")
            else:
                lines.append(f"    {edge.from_node} --> {edge.to_node}")

        return lines

    def _generate_styles(
        self,
        graph: ExecutionGraph,
        highlight_path: Optional[List[str]] = None
    ) -> List[str]:
        """Generate style definitions."""
        lines = ["    %% Style definitions"]

        # Add styles for each node type
        for node_id, node in graph.nodes.items():
            # Check if this node is in highlight path
            if highlight_path and node_id in highlight_path:
                # Highlighted style (bright yellow/gold)
                lines.append(f"    style {node_id} fill:#ffeb3b,stroke:#f57f17,stroke-width:3px")
            else:
                # Regular style based on node type
                color = self.colors.get(node.type.value, "#f9f9f9")
                lines.append(f"    style {node_id} fill:{color},stroke:#333,stroke-width:2px")

        return lines

    def _truncate_action(self, action: str, max_length: int) -> str:
        """Truncate action text to maximum length."""
        if len(action) <= max_length:
            return action

        return action[:max_length - 3] + "..."

    def _wrap_in_html(self, mermaid_content: str) -> str:
        """Wrap Mermaid content in HTML for viewing."""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Soplex SOP Visualization</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        .mermaid {{
            text-align: center;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .info {{
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Soplex SOP Visualization</h1>
        <p>Interactive flowchart showing SOP execution flow</p>
    </div>

    <div class="info">
        <strong>Legend:</strong>
        <span style="background-color: {self.colors.get('llm', '#cce5ff')}; padding: 2px 8px; margin: 0 5px;">🧠 LLM</span>
        <span style="background-color: {self.colors.get('code', '#d4edda')}; padding: 2px 8px; margin: 0 5px;">⚡ CODE</span>
        <span style="background-color: {self.colors.get('hybrid', '#fff3cd')}; padding: 2px 8px; margin: 0 5px;">🔀 HYBRID</span>
        <span style="background-color: {self.colors.get('branch', '#d4edda')}; padding: 2px 8px; margin: 0 5px;">🔀 BRANCH</span>
        <span style="background-color: {self.colors.get('escalate', '#f8d7da')}; padding: 2px 8px; margin: 0 5px;">🚨 ESCALATE</span>
        <span style="background-color: {self.colors.get('end', '#e2e3e5')}; padding: 2px 8px; margin: 0 5px;">🏁 END</span>
    </div>

    <div class="mermaid">
{mermaid_content}
    </div>

    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
</body>
</html>"""


def generate_sop_flowchart(
    graph: ExecutionGraph,
    title: Optional[str] = None,
    output_file: Optional[Path] = None,
    format: str = "mmd",
    execution_path: Optional[List[str]] = None
) -> str:
    """
    Convenience function to generate SOP flowchart.

    Args:
        graph: Execution graph to visualize
        title: Optional title
        output_file: Optional output file path
        format: Output format ("mmd" or "html")
        execution_path: Optional execution path to highlight

    Returns:
        Generated Mermaid content
    """
    generator = MermaidGenerator()

    if execution_path:
        mermaid_content = generator.generate_with_execution_path(
            graph, execution_path, title
        )
    else:
        mermaid_content = generator.generate_flowchart(graph, title)

    if output_file:
        generator.save_to_file(mermaid_content, output_file, format)

    return mermaid_content


def create_cost_comparison_chart(
    sessions_data: List[Dict[str, Any]],
    title: str = "Cost Comparison: LLM vs Hybrid"
) -> str:
    """
    Create a cost comparison chart using Mermaid.

    Args:
        sessions_data: List of session cost data
        title: Chart title

    Returns:
        Mermaid chart content
    """
    if not sessions_data:
        return "graph TD\n    A[No data available]"

    lines = [
        "%%{init: {'theme':'base', 'themeVariables': {'primaryColor':'#cce5ff'}}}%%",
        "graph TD",
        f"    title[\"{title}\"]",
        "",
        "    subgraph Costs[\"Cost Analysis\"]",
        "        direction TB",
    ]

    # Calculate totals
    total_hybrid = sum(s.get("total_cost", 0) for s in sessions_data)
    total_pure_llm = sum(s.get("pure_llm_cost", 0) for s in sessions_data)
    total_savings = total_pure_llm - total_hybrid

    lines.extend([
        f"        PureLLM[\"Pure LLM<br/>${total_pure_llm:.4f}\"]",
        f"        Hybrid[\"Hybrid Approach<br/>${total_hybrid:.4f}\"]",
        f"        Savings[\"💰 Savings<br/>${total_savings:.4f}<br/>({(total_savings/total_pure_llm*100):.1f}%)\"]",
        "",
        "        PureLLM -.-> Hybrid",
        "        PureLLM --> Savings",
        "    end",
        "",
        "    style PureLLM fill:#ffcccb",
        "    style Hybrid fill:#d4edda",
        "    style Savings fill:#fff3cd",
    ])

    return "\n".join(lines)
"""
Graph builder for soplex.
Converts SOPDefinition objects into executable ExecutionGraph objects.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from ..parser.models import SOPDefinition, Step, StepType
from .graph import ExecutionGraph, Node, Edge, NodeType
from .code_generator import CodeGenerator


class GraphBuilder:
    """
    Builds executable graphs from parsed SOP definitions.
    Handles step linking, branch resolution, and code generation.
    """

    def __init__(self):
        self.code_generator = CodeGenerator()

    def build_graph(self, sop_def: SOPDefinition) -> ExecutionGraph:
        """
        Build an execution graph from a SOP definition.

        Args:
            sop_def: Parsed SOP definition

        Returns:
            Executable graph ready for runtime
        """
        # Create graph
        graph = ExecutionGraph(
            name=sop_def.name,
            sop_source=sop_def.source_text,
            compilation_timestamp=datetime.now().isoformat(),
            tools_required=sop_def.tools.copy(),
        )

        # Convert steps to nodes
        self._create_nodes(graph, sop_def)

        # Generate code for deterministic steps
        self._generate_step_code(graph, sop_def.steps)

        # Create edges between nodes
        self._create_edges(graph, sop_def)

        # Validate and return
        issues = graph.validate()
        if issues:
            print(f"Warning: Graph validation issues: {issues}")

        return graph

    def _create_nodes(self, graph: ExecutionGraph, sop_def: SOPDefinition) -> None:
        """Create nodes from SOP steps."""
        for step in sop_def.steps:
            node_type = self._step_type_to_node_type(step.type)

            # For BRANCH nodes, we need to provide the condition up front
            condition = None
            yes_action = None
            no_action = None

            if step.branch:
                condition = step.branch.condition
                yes_action = step.branch.yes_action
                no_action = step.branch.no_action
            elif node_type == NodeType.BRANCH:
                # If classified as BRANCH but no explicit branch object,
                # use the action itself as condition
                condition = step.action

            node = Node(
                id=step.id,
                type=node_type,
                action=step.action,
                step_number=step.number,
                tools_required=step.tools_required,
                confidence=step.confidence,
                keywords=step.keywords,
                condition=condition,
                yes_action=yes_action,
                no_action=no_action,
            )

            graph.add_node(node)

    def _step_type_to_node_type(self, step_type: StepType) -> NodeType:
        """Convert StepType to NodeType."""
        mapping = {
            StepType.LLM: NodeType.LLM,
            StepType.CODE: NodeType.CODE,
            StepType.HYBRID: NodeType.HYBRID,
            StepType.BRANCH: NodeType.BRANCH,
            StepType.END: NodeType.END,
            StepType.ESCALATE: NodeType.ESCALATE,
        }
        return mapping[step_type]

    def _generate_step_code(self, graph: ExecutionGraph, steps: List[Step]) -> None:
        """Generate code for steps that need it."""
        handlers = self.code_generator.generate_all_handlers(steps)

        # Add generated code to nodes
        for step_id, handler_code in handlers.items():
            node = graph.get_node(step_id)
            if node:
                node.handler_code = handler_code

    def _create_edges(self, graph: ExecutionGraph, sop_def: SOPDefinition) -> None:
        """Create edges between nodes based on SOP flow."""
        for i, step in enumerate(sop_def.steps):
            current_node_id = step.id

            if step.type == StepType.BRANCH and step.branch:
                # Handle branching step
                self._create_branch_edges(graph, step, sop_def.steps)
            elif step.type in [StepType.END, StepType.ESCALATE]:
                # Terminal steps - no outgoing edges
                continue
            else:
                # Linear step - connect to next step
                if i + 1 < len(sop_def.steps):
                    next_step = sop_def.steps[i + 1]
                    edge = Edge(
                        from_node=current_node_id,
                        to_node=next_step.id,
                        condition_type="always"
                    )
                    graph.add_edge(edge)

    def _create_branch_edges(self, graph: ExecutionGraph, branch_step: Step, all_steps: List[Step]) -> None:
        """Create edges for a branching step."""
        if not branch_step.branch:
            return

        branch = branch_step.branch
        current_node_id = branch_step.id

        # Find target steps for YES and NO branches
        yes_target = self._find_branch_target(branch.yes_action, all_steps)
        no_target = self._find_branch_target(branch.no_action, all_steps)

        # Create YES edge
        if yes_target:
            yes_edge = Edge(
                from_node=current_node_id,
                to_node=yes_target.id,
                condition_type="yes",
                label="YES"
            )
            graph.add_edge(yes_edge)

        # Create NO edge
        if no_target:
            no_edge = Edge(
                from_node=current_node_id,
                to_node=no_target.id,
                condition_type="no",
                label="NO"
            )
            graph.add_edge(no_edge)

        # If no explicit targets found, connect to next sequential step
        if not yes_target and not no_target:
            # Find the next step after this branch
            branch_index = next((i for i, step in enumerate(all_steps) if step.id == current_node_id), -1)
            if branch_index >= 0 and branch_index + 1 < len(all_steps):
                next_step = all_steps[branch_index + 1]

                # Connect both YES and NO to next step (fallback behavior)
                yes_edge = Edge(from_node=current_node_id, to_node=next_step.id, condition_type="yes")
                no_edge = Edge(from_node=current_node_id, to_node=next_step.id, condition_type="no")
                graph.add_edge(yes_edge)
                graph.add_edge(no_edge)

    def _find_branch_target(self, action: str, all_steps: List[Step]) -> Optional[Step]:
        """
        Find the target step for a branch action.

        Args:
            action: Branch action text (e.g., "go to step 5", "end")
            all_steps: All available steps

        Returns:
            Target step or None if not found
        """
        action_lower = action.lower().strip()

        # Check for explicit step references
        import re
        step_match = re.search(r'step\s+(\d+)', action_lower)
        if step_match:
            step_num = int(step_match.group(1))
            for step in all_steps:
                if step.number == step_num:
                    return step

        # Check for "proceed to step X"
        proceed_match = re.search(r'proceed\s+to\s+step\s+(\d+)', action_lower)
        if proceed_match:
            step_num = int(proceed_match.group(1))
            for step in all_steps:
                if step.number == step_num:
                    return step

        # Check for end conditions
        if any(keyword in action_lower for keyword in ['end', 'complete', 'done', 'finish', 'close']):
            for step in all_steps:
                if step.type == StepType.END:
                    return step

        # Check for escalation conditions
        if any(keyword in action_lower for keyword in ['escalate', 'hand off', 'transfer', 'supervisor']):
            for step in all_steps:
                if step.type == StepType.ESCALATE:
                    return step

        return None

    def create_linear_graph(self, sop_def: SOPDefinition) -> ExecutionGraph:
        """
        Create a simple linear graph (for testing/fallback).

        Args:
            sop_def: SOP definition

        Returns:
            Linear execution graph
        """
        graph = ExecutionGraph(
            name=f"{sop_def.name} (Linear)",
            sop_source=sop_def.source_text,
            compilation_timestamp=datetime.now().isoformat(),
            tools_required=sop_def.tools.copy(),
        )

        # Create nodes
        self._create_nodes(graph, sop_def)

        # Generate code
        self._generate_step_code(graph, sop_def.steps)

        # Create linear edges (ignore branching)
        for i in range(len(sop_def.steps) - 1):
            current_step = sop_def.steps[i]
            next_step = sop_def.steps[i + 1]

            edge = Edge(
                from_node=current_step.id,
                to_node=next_step.id,
                condition_type="always"
            )
            graph.add_edge(edge)

        return graph

    def optimize_graph(self, graph: ExecutionGraph) -> ExecutionGraph:
        """
        Optimize the graph for better execution.

        Args:
            graph: Input graph

        Returns:
            Optimized graph
        """
        # TODO: Implement graph optimizations
        # - Remove redundant nodes
        # - Merge sequential LLM calls
        # - Optimize branching logic
        # - Cache frequently accessed data

        return graph

    def analyze_graph_complexity(self, graph: ExecutionGraph) -> Dict[str, Any]:
        """
        Analyze graph complexity metrics.

        Args:
            graph: Execution graph

        Returns:
            Complexity analysis
        """
        analysis = {
            "total_nodes": len(graph.nodes),
            "total_edges": len(graph.edges),
            "branch_points": 0,
            "terminal_nodes": 0,
            "max_path_length": 0,
            "cyclic": False,
        }

        # Count node types
        for node in graph.nodes.values():
            if node.type == NodeType.BRANCH:
                analysis["branch_points"] += 1
            elif node.type in [NodeType.END, NodeType.ESCALATE]:
                analysis["terminal_nodes"] += 1

        # Calculate complexity score
        complexity_score = (
            analysis["total_nodes"] * 1 +
            analysis["branch_points"] * 3 +
            analysis["total_edges"] * 0.5
        )
        analysis["complexity_score"] = complexity_score

        # Categorize complexity
        if complexity_score <= 10:
            analysis["complexity_level"] = "simple"
        elif complexity_score <= 30:
            analysis["complexity_level"] = "moderate"
        else:
            analysis["complexity_level"] = "complex"

        return analysis
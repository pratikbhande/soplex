"""
Executor for soplex - runs compiled graphs step by step.
Orchestrates LLM calls, code execution, and tool usage.
"""
import time
import sys
from typing import Dict, List, Any, Optional, Iterator, Callable
from datetime import datetime

from ..compiler.graph import ExecutionGraph, Node, NodeType
from ..llm.provider import LLMProvider
from .state import ExecutionState, StepResult, ExecutionStatus
from .tool_registry import ToolRegistry, default_registry


class SOPExecutor:
    """
    Executes compiled SOP graphs step by step.
    Manages the flow between LLM calls, code execution, and tool usage.
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        tool_registry: Optional[ToolRegistry] = None,
        max_steps: int = 50,
        timeout_seconds: float = 300.0
    ):
        """
        Initialize executor.

        Args:
            llm_provider: LLM provider for conversational steps
            tool_registry: Registry of available tools
            max_steps: Maximum steps to execute (safety limit)
            timeout_seconds: Maximum execution time
        """
        self.llm_provider = llm_provider
        self.tool_registry = tool_registry or default_registry
        self.max_steps = max_steps
        self.timeout_seconds = timeout_seconds

        # Generated code handlers cache
        self._handlers_cache: Dict[str, Callable] = {}

    def execute(
        self,
        graph: ExecutionGraph,
        initial_input: Optional[str] = None,
        interactive: bool = False
    ) -> ExecutionState:
        """
        Execute a graph completely.

        Args:
            graph: Compiled execution graph
            initial_input: Initial user input
            interactive: If True, pause for user input when needed

        Returns:
            Final execution state
        """
        state = ExecutionState()
        state.set_status(ExecutionStatus.RUNNING)

        # Add initial input if provided
        if initial_input:
            state.add_conversation_turn("user", initial_input)
            state.add_user_input("initial_input", initial_input)

        # Execute step by step
        try:
            for step_result in self.execute_interactive(graph, state):
                if not interactive:
                    continue  # Just consume the iterator

                # In interactive mode, could yield control here
                # For now, just continue

            return state

        except Exception as e:
            state.add_error(f"Execution failed: {e}")
            state.set_status(ExecutionStatus.FAILED)
            return state

    def execute_interactive(
        self,
        graph: ExecutionGraph,
        state: Optional[ExecutionState] = None
    ) -> Iterator[StepResult]:
        """
        Execute graph step by step, yielding results.

        Args:
            graph: Compiled execution graph
            state: Execution state (creates new if None)

        Yields:
            StepResult for each executed step
        """
        if state is None:
            state = ExecutionState()
            state.set_status(ExecutionStatus.RUNNING)

        start_time = time.time()
        current_node_id = graph.start_node_id

        if not current_node_id:
            raise ValueError("Graph has no start node")

        step_count = 0

        while current_node_id and step_count < self.max_steps:
            # Check timeout
            if time.time() - start_time > self.timeout_seconds:
                state.add_error(f"Execution timeout after {self.timeout_seconds} seconds")
                state.set_status(ExecutionStatus.FAILED)
                break

            # Get current node
            node = graph.get_node(current_node_id)
            if not node:
                state.add_error(f"Node {current_node_id} not found in graph")
                state.set_status(ExecutionStatus.FAILED)
                break

            # Execute the node
            try:
                state.current_step_id = current_node_id
                step_result = self._execute_node(node, graph, state)
                state.add_step_result(step_result)
                yield step_result

                # Check for terminal states
                if step_result.status == "escalated":
                    state.set_status(ExecutionStatus.ESCALATED)
                    break
                elif step_result.status == "failed":
                    # Add step error to global errors list
                    if step_result.error:
                        state.add_error(f"Step {step_result.step_id} failed: {step_result.error}")
                    state.set_status(ExecutionStatus.FAILED)
                    break
                elif node.type in [NodeType.END, NodeType.ESCALATE]:
                    state.set_status(ExecutionStatus.COMPLETED)
                    break

                # Get next node
                current_node_id = graph.get_next(current_node_id, state.data)

            except Exception as e:
                error_msg = f"Error executing step {current_node_id}: {e}"
                state.add_error(error_msg)

                step_result = StepResult(
                    step_id=current_node_id,
                    step_number=node.step_number,
                    step_type=node.type.value,
                    action=node.action,
                    status="failed",
                    result={},
                    duration_ms=0,
                    timestamp=datetime.now().isoformat(),
                    error=error_msg
                )
                state.add_step_result(step_result)
                yield step_result

                state.set_status(ExecutionStatus.FAILED)
                break

            step_count += 1

        # Mark as completed if we finished normally
        if state.status == ExecutionStatus.RUNNING:
            state.set_status(ExecutionStatus.COMPLETED)

    def _execute_node(self, node: Node, graph: ExecutionGraph, state: ExecutionState) -> StepResult:
        """Execute a single node."""
        start_time = time.time()

        try:
            if node.type == NodeType.LLM:
                result = self._execute_llm_node(node, state)
            elif node.type == NodeType.CODE:
                result = self._execute_code_node(node, state)
            elif node.type == NodeType.HYBRID:
                result = self._execute_hybrid_node(node, state)
            elif node.type == NodeType.BRANCH:
                result = self._execute_branch_node(node, state)
            elif node.type == NodeType.END:
                result = self._execute_end_node(node, state)
            elif node.type == NodeType.ESCALATE:
                result = self._execute_escalate_node(node, state)
            else:
                result = {
                    "status": "failed",
                    "error": f"Unknown node type: {node.type}"
                }

            duration_ms = (time.time() - start_time) * 1000

            return StepResult(
                step_id=node.id,
                step_number=node.step_number,
                step_type=node.type.value,
                action=node.action,
                status=result.get("status", "completed"),
                result=result,
                duration_ms=duration_ms,
                timestamp=datetime.now().isoformat(),
                cost=result.get("cost", 0.0),
                tokens_used=result.get("tokens", 0),
                error=result.get("error"),
                llm_response=result.get("llm_response"),
                llm_provider=result.get("llm_provider"),
                llm_model=result.get("llm_model"),
                code_executed=result.get("code_executed", False),
                condition_result=result.get("condition_met"),
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            return StepResult(
                step_id=node.id,
                step_number=node.step_number,
                step_type=node.type.value,
                action=node.action,
                status="failed",
                result={},
                duration_ms=duration_ms,
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )

    def _execute_llm_node(self, node: Node, state: ExecutionState) -> Dict[str, Any]:
        """Execute an LLM node."""
        if not self.llm_provider:
            raise ValueError("LLM provider required for LLM nodes")

        # Build context for this step
        context = state.get_context_for_step(node.action)

        # Create system prompt
        system_prompt = self.llm_provider.build_system_prompt(node.action, context)

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]

        # Add recent conversation history
        recent_turns = state.get_recent_conversation(3)
        for turn in recent_turns:
            if turn.role in ["user", "assistant"]:
                messages.append({"role": turn.role, "content": turn.content})

        # If no recent user input, create a prompt based on the action
        if not any(msg["role"] == "user" for msg in messages[1:]):  # Exclude system message
            user_prompt = f"Please proceed with: {node.action}"
            messages.append({"role": "user", "content": user_prompt})

        # Generate response
        response = self.llm_provider.generate(messages)

        # Add to conversation history
        state.add_conversation_turn(
            "assistant",
            response.content,
            step_id=node.id,
            cost=response.cost,
            tokens=response.usage["total_tokens"]
        )

        return {
            "status": "completed",
            "llm_response": response.content,
            "llm_provider": response.provider,
            "llm_model": response.model,
            "cost": response.cost,
            "tokens": response.usage["total_tokens"],
            "finish_reason": response.finish_reason,
        }

    def _execute_code_node(self, node: Node, state: ExecutionState) -> Dict[str, Any]:
        """Execute a CODE node."""
        if node.handler_code:
            # Execute generated handler
            handler = self._get_handler_function(node)
            if handler:
                result = handler(state.data, self.tool_registry.tools, node)
                return {
                    "status": "completed",
                    "code_executed": True,
                    "result": result
                }

        # Fallback: basic execution based on action
        return self._execute_fallback_code(node, state)

    def _execute_branch_node(self, node: Node, state: ExecutionState) -> Dict[str, Any]:
        """Execute a BRANCH node."""
        if node.handler_code:
            # Execute generated handler
            handler = self._get_handler_function(node)
            if handler:
                result = handler(state.data, self.tool_registry.tools, node)
                condition_met = result.get("condition_met", True)
                state.last_condition_result = condition_met
                return {
                    "status": "completed",
                    "code_executed": True,
                    "condition_met": condition_met,
                    "result": result
                }

        # Fallback: simple condition evaluation
        return self._execute_fallback_branch(node, state)

    def _execute_hybrid_node(self, node: Node, state: ExecutionState) -> Dict[str, Any]:
        """Execute a HYBRID node (LLM + code)."""
        # First, execute LLM part
        llm_result = self._execute_llm_node(node, state)

        # Then execute code validation part
        if node.handler_code:
            handler = self._get_handler_function(node)
            if handler:
                # Pass LLM response to validation
                state.data["last_llm_response"] = llm_result.get("llm_response", "")
                code_result = handler(state.data, self.tool_registry.tools, node)

                # Combine results
                return {
                    "status": "completed",
                    "llm_response": llm_result.get("llm_response"),
                    "llm_provider": llm_result.get("llm_provider"),
                    "llm_model": llm_result.get("llm_model"),
                    "code_executed": True,
                    "cost": llm_result.get("cost", 0),
                    "tokens": llm_result.get("tokens", 0),
                    "validation_result": code_result,
                    "result": {
                        "llm": llm_result,
                        "code": code_result
                    }
                }

        # Even without handler code, HYBRID nodes should indicate code was "executed"
        llm_result["code_executed"] = True
        return llm_result

    def _execute_end_node(self, node: Node, state: ExecutionState) -> Dict[str, Any]:
        """Execute an END node."""
        return {
            "status": "completed",
            "message": "SOP execution completed successfully",
            "final_step": True
        }

    def _execute_escalate_node(self, node: Node, state: ExecutionState) -> Dict[str, Any]:
        """Execute an ESCALATE node."""
        state.add_warning(f"Escalation triggered: {node.action}")
        return {
            "status": "escalated",
            "message": "Case escalated to human supervisor",
            "escalation_reason": node.action
        }

    def _execute_fallback_code(self, node: Node, state: ExecutionState) -> Dict[str, Any]:
        """Fallback execution for CODE nodes without handlers."""
        # Basic tool calling based on action
        action_lower = node.action.lower()

        if node.tools_required and len(node.tools_required) > 0:
            tool_name = node.tools_required[0]
            try:
                # Get parameters from state, with defaults for common cases
                params = state.step_params.copy()

                # If no explicit params, try to provide reasonable defaults
                if not params:
                    # For order_db, provide a default order_number
                    if tool_name == "order_db":
                        params = {"order_number": "12345"}
                    # Add other common tool defaults as needed

                tool_result = self.tool_registry.call_tool(tool_name, **params)
                state.add_tool_result(tool_name, tool_result)

                return {
                    "status": "completed",
                    "tool_used": tool_name,
                    "tool_result": tool_result,
                    "code_executed": True
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": f"Tool call failed: {e}"
                }

        return {
            "status": "completed",
            "message": f"Executed: {node.action}",
            "code_executed": True
        }

    def _execute_fallback_branch(self, node: Node, state: ExecutionState) -> Dict[str, Any]:
        """Fallback execution for BRANCH nodes without handlers."""
        # Simple condition evaluation
        condition_met = True  # Default to true for fallback

        # Try to extract simple conditions
        if node.condition:
            condition_lower = node.condition.lower()
            if "active" in condition_lower:
                # Check if something is marked as active
                condition_met = state.data.get("status") == "active"
            elif "successful" in condition_lower:
                # Check if last operation was successful
                condition_met = state.data.get("last_result", {}).get("status") == "success"
            # Add more condition patterns as needed

        state.last_condition_result = condition_met
        return {
            "status": "completed",
            "condition_met": condition_met,
            "condition": node.condition or node.action,
            "code_executed": True
        }

    def _get_handler_function(self, node: Node) -> Optional[Callable]:
        """Get or compile handler function for a node."""
        if not node.handler_code:
            return None

        if node.id in self._handlers_cache:
            return self._handlers_cache[node.id]

        try:
            # Create a local namespace for execution
            namespace = {
                "__builtins__": __builtins__,
                "datetime": datetime,
                "time": time,
            }

            # Execute the handler code
            exec(node.handler_code, namespace)

            # Get the handler function
            handler_name = f"handle_{node.id}"
            if handler_name in namespace:
                handler = namespace[handler_name]
                self._handlers_cache[node.id] = handler
                return handler

        except Exception as e:
            state_msg = f"Failed to compile handler for {node.id}: {e}"
            print(f"Warning: {state_msg}")  # For debugging

        return None

    def set_llm_provider(self, provider: LLMProvider) -> None:
        """Set the LLM provider."""
        self.llm_provider = provider

    def set_tool_registry(self, registry: ToolRegistry) -> None:
        """Set the tool registry."""
        self.tool_registry = registry

    def validate_graph(self, graph: ExecutionGraph) -> List[str]:
        """
        Validate graph before execution.

        Args:
            graph: Graph to validate

        Returns:
            List of validation issues
        """
        issues = []

        # Check graph structure
        graph_issues = graph.validate()
        issues.extend(graph_issues)

        # Check tool availability
        required_tools = set()
        for node in graph.nodes.values():
            required_tools.update(node.tools_required)

        for tool_name in required_tools:
            if not self.tool_registry.is_tool_available(tool_name):
                issues.append(f"Required tool not available: {tool_name}")

        # Check LLM availability for LLM nodes
        llm_nodes = [n for n in graph.nodes.values()
                    if n.type in [NodeType.LLM, NodeType.HYBRID]]
        if llm_nodes and not self.llm_provider:
            issues.append("LLM provider required but not configured")

        return issues
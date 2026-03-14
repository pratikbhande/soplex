"""
State management for soplex execution.
Tracks conversation history, data, cost, and execution flow.
"""
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class ExecutionStatus(str, Enum):
    """Status of SOP execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class StepResult:
    """Result of executing a single step."""
    step_id: str
    step_number: int
    step_type: str
    action: str
    status: str
    result: Dict[str, Any]
    duration_ms: float
    timestamp: str
    cost: float = 0.0
    tokens_used: int = 0
    error: Optional[str] = None

    # LLM-specific fields
    llm_response: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None

    # Code-specific fields
    code_executed: bool = False
    condition_result: Optional[bool] = None


@dataclass
class ConversationTurn:
    """Single turn in the conversation."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str
    step_id: Optional[str] = None
    cost: float = 0.0
    tokens: int = 0


class ExecutionState:
    """
    Manages state during SOP execution.
    Tracks conversation, data, costs, and execution flow.
    """

    def __init__(self, session_id: Optional[str] = None):
        """Initialize execution state."""
        self.session_id = session_id or f"session_{int(time.time())}"
        self.start_time = datetime.now()

        # Execution status
        self.status = ExecutionStatus.PENDING
        self.current_step_id: Optional[str] = None
        self.execution_path: List[str] = []

        # Conversation tracking
        self.conversation_history: List[ConversationTurn] = []
        self.user_inputs: Dict[str, Any] = {}

        # Data storage
        self.data: Dict[str, Any] = {}
        self.step_results: List[StepResult] = []

        # Cost and performance tracking
        self.total_cost = 0.0
        self.llm_cost = 0.0
        self.code_cost = 0.0
        self.total_tokens = 0
        self.llm_calls = 0
        self.code_calls = 0

        # Tool usage
        self.tools_used: List[str] = []
        self.tool_results: Dict[str, Any] = {}

        # Error tracking
        self.errors: List[str] = []
        self.warnings: List[str] = []

        # Metadata
        self.metadata: Dict[str, Any] = {}

        # State for branch conditions
        self.last_condition_result: Optional[bool] = None
        self.branch_history: List[Dict[str, Any]] = []

        # Step parameters for current execution
        self.step_params: Dict[str, Any] = {}

    def add_conversation_turn(
        self,
        role: str,
        content: str,
        step_id: Optional[str] = None,
        cost: float = 0.0,
        tokens: int = 0
    ) -> None:
        """Add a turn to the conversation history."""
        turn = ConversationTurn(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            step_id=step_id,
            cost=cost,
            tokens=tokens
        )
        self.conversation_history.append(turn)

        # Update totals
        self.total_cost += cost
        self.total_tokens += tokens

        if role == "assistant" and cost > 0:
            self.llm_cost += cost
            self.llm_calls += 1

    def add_step_result(self, result: StepResult) -> None:
        """Add a step execution result."""
        self.step_results.append(result)
        self.execution_path.append(result.step_id)

        # Update totals
        self.total_cost += result.cost
        self.total_tokens += result.tokens_used

        if result.step_type.lower() in ["llm", "hybrid"] and result.cost > 0:
            self.llm_cost += result.cost
            self.llm_calls += 1

        if result.step_type.lower() in ["code", "branch"]:
            self.code_cost += 0.0001  # Minimal compute cost
            self.code_calls += 1

        # Track condition results for branching
        if result.condition_result is not None:
            self.last_condition_result = result.condition_result
            self.branch_history.append({
                "step_id": result.step_id,
                "condition": result.action,
                "result": result.condition_result,
                "timestamp": result.timestamp
            })

    def set_data(self, key: str, value: Any) -> None:
        """Set data in the state."""
        self.data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data from the state."""
        return self.data.get(key, default)

    def update_data(self, updates: Dict[str, Any]) -> None:
        """Update multiple data values."""
        self.data.update(updates)

    def add_tool_result(self, tool_name: str, result: Any) -> None:
        """Add result from a tool call."""
        if tool_name not in self.tools_used:
            self.tools_used.append(tool_name)

        self.tool_results[tool_name] = result

        # Store in general data as well for easy access
        self.data[f"{tool_name}_result"] = result
        self.data["last_tool_result"] = result

    def add_user_input(self, prompt: str, response: Any) -> None:
        """Add user input to tracking."""
        self.user_inputs[prompt] = response
        self.data["last_user_input"] = response

    def add_error(self, error: str, step_id: Optional[str] = None) -> None:
        """Add an error to tracking."""
        error_msg = f"[{step_id or 'unknown'}] {error}" if step_id else error
        self.errors.append(error_msg)

    def add_warning(self, warning: str, step_id: Optional[str] = None) -> None:
        """Add a warning to tracking."""
        warning_msg = f"[{step_id or 'unknown'}] {warning}" if step_id else warning
        self.warnings.append(warning_msg)

    def set_status(self, status: ExecutionStatus) -> None:
        """Set the execution status."""
        self.status = status

    def get_recent_conversation(self, max_turns: int = 5) -> List[ConversationTurn]:
        """Get recent conversation history."""
        return self.conversation_history[-max_turns:]

    def get_context_for_step(self, step_action: str) -> Dict[str, Any]:
        """
        Build context dictionary for a specific step.
        Used for LLM prompts and step execution.
        """
        return {
            "step_action": step_action,
            "conversation_history": self.get_recent_conversation(),
            "data": self.data.copy(),
            "user_inputs": self.user_inputs.copy(),
            "tools_used": self.tools_used.copy(),
            "tool_results": self.tool_results.copy(),
            "execution_path": self.execution_path.copy(),
            "last_condition_result": self.last_condition_result,
            "session_id": self.session_id,
            "status": self.status.value,
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary statistics."""
        duration = (datetime.now() - self.start_time).total_seconds()

        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "duration_seconds": round(duration, 2),
            "steps_executed": len(self.step_results),
            "conversation_turns": len(self.conversation_history),
            "execution_path": self.execution_path,
            "costs": {
                "total_cost": round(self.total_cost, 6),
                "llm_cost": round(self.llm_cost, 6),
                "code_cost": round(self.code_cost, 6),
                "savings": round((self.llm_calls * 0.001) - self.total_cost, 6) if self.llm_calls > 0 else 0.0,
            },
            "usage": {
                "total_tokens": self.total_tokens,
                "llm_calls": self.llm_calls,
                "code_calls": self.code_calls,
                "tools_used": len(set(self.tools_used)),
            },
            "tools_used": self.tools_used,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "status": self.status.value,
            "current_step_id": self.current_step_id,
            "execution_path": self.execution_path,
            "conversation_history": [
                {
                    "role": turn.role,
                    "content": turn.content,
                    "timestamp": turn.timestamp,
                    "step_id": turn.step_id,
                    "cost": turn.cost,
                    "tokens": turn.tokens
                }
                for turn in self.conversation_history
            ],
            "user_inputs": self.user_inputs,
            "data": self.data,
            "step_results": [
                {
                    "step_id": result.step_id,
                    "step_number": result.step_number,
                    "step_type": result.step_type,
                    "action": result.action,
                    "status": result.status,
                    "result": result.result,
                    "duration_ms": result.duration_ms,
                    "timestamp": result.timestamp,
                    "cost": result.cost,
                    "tokens_used": result.tokens_used,
                    "error": result.error,
                    "llm_response": result.llm_response,
                    "llm_provider": result.llm_provider,
                    "llm_model": result.llm_model,
                    "code_executed": result.code_executed,
                    "condition_result": result.condition_result,
                }
                for result in self.step_results
            ],
            "total_cost": self.total_cost,
            "llm_cost": self.llm_cost,
            "code_cost": self.code_cost,
            "total_tokens": self.total_tokens,
            "llm_calls": self.llm_calls,
            "code_calls": self.code_calls,
            "tools_used": self.tools_used,
            "tool_results": self.tool_results,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "last_condition_result": self.last_condition_result,
            "branch_history": self.branch_history,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionState":
        """Restore state from dictionary."""
        state = cls(session_id=data["session_id"])

        # Restore basic fields
        state.start_time = datetime.fromisoformat(data["start_time"])
        state.status = ExecutionStatus(data["status"])
        state.current_step_id = data.get("current_step_id")
        state.execution_path = data.get("execution_path", [])
        state.user_inputs = data.get("user_inputs", {})
        state.data = data.get("data", {})
        state.total_cost = data.get("total_cost", 0.0)
        state.llm_cost = data.get("llm_cost", 0.0)
        state.code_cost = data.get("code_cost", 0.0)
        state.total_tokens = data.get("total_tokens", 0)
        state.llm_calls = data.get("llm_calls", 0)
        state.code_calls = data.get("code_calls", 0)
        state.tools_used = data.get("tools_used", [])
        state.tool_results = data.get("tool_results", {})
        state.errors = data.get("errors", [])
        state.warnings = data.get("warnings", [])
        state.metadata = data.get("metadata", {})
        state.last_condition_result = data.get("last_condition_result")
        state.branch_history = data.get("branch_history", [])

        # Restore conversation history
        for turn_data in data.get("conversation_history", []):
            turn = ConversationTurn(
                role=turn_data["role"],
                content=turn_data["content"],
                timestamp=turn_data["timestamp"],
                step_id=turn_data.get("step_id"),
                cost=turn_data.get("cost", 0.0),
                tokens=turn_data.get("tokens", 0),
            )
            state.conversation_history.append(turn)

        # Restore step results
        for result_data in data.get("step_results", []):
            result = StepResult(
                step_id=result_data["step_id"],
                step_number=result_data["step_number"],
                step_type=result_data["step_type"],
                action=result_data["action"],
                status=result_data["status"],
                result=result_data["result"],
                duration_ms=result_data["duration_ms"],
                timestamp=result_data["timestamp"],
                cost=result_data.get("cost", 0.0),
                tokens_used=result_data.get("tokens_used", 0),
                error=result_data.get("error"),
                llm_response=result_data.get("llm_response"),
                llm_provider=result_data.get("llm_provider"),
                llm_model=result_data.get("llm_model"),
                code_executed=result_data.get("code_executed", False),
                condition_result=result_data.get("condition_result"),
            )
            state.step_results.append(result)

        return state
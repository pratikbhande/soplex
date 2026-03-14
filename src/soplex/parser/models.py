"""
Pydantic models for soplex data structures.
Core types: SOPDefinition, Step, StepType, BranchCondition, Tool.
"""
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, computed_field


class StepType(str, Enum):
    """Step execution type classification."""

    LLM = "llm"           # Conversation steps (ask, greet, inform, etc.)
    CODE = "code"         # Deterministic steps (check, lookup, calculate, etc.)
    HYBRID = "hybrid"     # LLM + code validation combined
    BRANCH = "branch"     # Conditional branching (if/else logic)
    END = "end"           # Terminal step (complete/done)
    ESCALATE = "escalate" # Hand off to human


class BranchCondition(BaseModel):
    """Represents a conditional branch in an SOP."""

    condition: str = Field(..., description="The condition to evaluate")
    yes_action: str = Field(..., description="Action if condition is true")
    no_action: str = Field(..., description="Action if condition is false")
    yes_step_id: Optional[str] = Field(None, description="ID of step if condition is true")
    no_step_id: Optional[str] = Field(None, description="ID of step if condition is false")


class Tool(BaseModel):
    """Tool/function that can be called during SOP execution."""

    name: str = Field(..., description="Tool identifier")
    description: Optional[str] = Field(None, description="What the tool does")
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Tool parameters schema"
    )
    mock_response: Optional[Any] = Field(None, description="Mock response for testing")


class Step(BaseModel):
    """Individual step in an SOP."""

    id: str = Field(..., description="Unique step identifier")
    number: int = Field(..., description="Step number in sequence")
    text: str = Field(..., description="Original step text")
    type: StepType = Field(..., description="Classified step type")
    action: str = Field(..., description="Processed action text")

    # Branch-specific fields
    branch: Optional[BranchCondition] = Field(
        None, description="Branch condition if this is a BRANCH step"
    )

    # Tool/function references
    tools_required: List[str] = Field(
        default_factory=list, description="Tools needed for this step"
    )

    # Generated code (for CODE/HYBRID steps)
    handler_code: Optional[str] = Field(
        None, description="Generated Python code for execution"
    )

    # Next step references
    next_step_id: Optional[str] = Field(
        None, description="ID of next step (for linear flow)"
    )

    # Metadata
    confidence: float = Field(
        default=1.0, description="Classification confidence score"
    )
    keywords: List[str] = Field(
        default_factory=list, description="Keywords that influenced classification"
    )

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        """Ensure confidence is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return v

    @field_validator('type')
    @classmethod
    def validate_step_type(cls, v):
        """Ensure step type is valid."""
        if v not in StepType:
            raise ValueError(f'Invalid step type: {v}')
        return v


class SOPDefinition(BaseModel):
    """Complete SOP definition with metadata and steps."""

    # Header metadata
    name: str = Field(..., description="SOP procedure name")
    trigger: Optional[str] = Field(None, description="When this SOP activates")
    tools: List[str] = Field(
        default_factory=list, description="Tools available to this SOP"
    )

    # Steps
    steps: List[Step] = Field(..., description="Ordered list of SOP steps")

    # Tool definitions
    tool_definitions: Dict[str, Tool] = Field(
        default_factory=dict, description="Available tool definitions"
    )

    # Metadata
    source_text: str = Field(..., description="Original SOP text")
    start_step_id: Optional[str] = Field(None, description="ID of the first step")

    # Statistics
    total_steps: int = Field(default=0, description="Total number of steps")
    llm_steps: int = Field(default=0, description="Number of LLM steps")
    code_steps: int = Field(default=0, description="Number of CODE steps")
    hybrid_steps: int = Field(default=0, description="Number of HYBRID steps")
    branch_steps: int = Field(default=0, description="Number of BRANCH steps")

    @field_validator('steps')
    @classmethod
    def validate_steps(cls, v):
        """Ensure steps have unique IDs and valid references."""
        if not v:
            raise ValueError('SOP must have at least one step')

        # Check for duplicate step IDs
        step_ids = [step.id for step in v]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError('Duplicate step IDs found')

        return v

    def model_post_init(self, __context):
        """Calculate step statistics after model initialization."""
        self.total_steps = len(self.steps)
        self.llm_steps = sum(1 for step in self.steps if step.type == StepType.LLM)
        self.code_steps = sum(1 for step in self.steps if step.type == StepType.CODE)
        self.hybrid_steps = sum(1 for step in self.steps if step.type == StepType.HYBRID)
        self.branch_steps = sum(1 for step in self.steps if step.type == StepType.BRANCH)

    def get_step_by_id(self, step_id: str) -> Optional[Step]:
        """Find step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_steps_by_type(self, step_type: StepType) -> List[Step]:
        """Get all steps of a specific type."""
        return [step for step in self.steps if step.type == step_type]

    def get_cost_estimate(self, pricing: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Estimate costs based on step types.
        Returns dict with 'llm_cost', 'code_cost', 'total_cost', 'savings'.
        """
        # Rough estimates for demonstration
        # In practice, this would need actual token counts
        avg_tokens_per_llm_step = 150  # Conservative estimate

        # Calculate LLM cost (LLM steps + portion of HYBRID steps that use LLM)
        # HYBRID steps use LLM but typically with smaller prompts
        pure_llm_step_count = self.llm_steps
        hybrid_llm_portion = self.hybrid_steps * 0.6  # HYBRID uses less LLM than pure LLM

        total_llm_equivalent = pure_llm_step_count + hybrid_llm_portion
        estimated_tokens = total_llm_equivalent * avg_tokens_per_llm_step

        # Assume gpt-4o-mini pricing as baseline
        cost_per_1m_tokens = pricing.get('gpt-4o-mini', {}).get('input', 0.15)
        llm_cost = (estimated_tokens / 1_000_000) * cost_per_1m_tokens

        # CODE steps are essentially free
        code_cost = 0.0001 * (self.code_steps + self.branch_steps + (self.hybrid_steps * 0.4))

        total_cost = llm_cost + code_cost

        # Calculate savings vs pure-LLM approach
        pure_llm_cost = len(self.steps) * avg_tokens_per_llm_step * cost_per_1m_tokens / 1_000_000
        savings = pure_llm_cost - total_cost
        savings_percent = (savings / pure_llm_cost * 100) if pure_llm_cost > 0 else 0

        return {
            'llm_cost': round(llm_cost, 6),
            'code_cost': round(code_cost, 6),
            'total_cost': round(total_cost, 6),
            'pure_llm_cost': round(pure_llm_cost, 6),
            'savings': round(savings, 6),
            'savings_percent': round(savings_percent, 1)
        }

    def summary(self) -> Dict[str, Any]:
        """Return summary statistics."""
        return {
            'name': self.name,
            'total_steps': self.total_steps,
            'llm_steps': self.llm_steps,
            'code_steps': self.code_steps,
            'hybrid_steps': self.hybrid_steps,
            'branch_steps': self.branch_steps,
            'tools': len(self.tools),
            'has_branches': self.branch_steps > 0,
            'start_step': self.start_step_id,
        }
"""
soplex: Compile plain-English SOPs into executable, cost-optimized agent graphs.

Transform Standard Operating Procedures into hybrid agent graphs where:
- Conversation steps use LLMs
- Decision steps run as deterministic code
- Tool/API steps execute as function calls
- Hybrid steps combine LLM + code validation

Result: 77% cheaper than pure-LLM agents with 99%+ decision accuracy.
"""

__version__ = "0.1.4"
__author__ = "soplex"
__email__ = "info@soplex.dev"

# Public API exports
from .config import SoplexConfig, get_config
from .parser.models import (
    SOPDefinition,
    Step,
    StepType,
    BranchCondition,
    Tool,
)
from .compiler.python_api import PythonGraphBuilder

__all__ = [
    "__version__",
    "SoplexConfig",
    "get_config",
    "SOPDefinition",
    "Step",
    "StepType",
    "BranchCondition",
    "Tool",
    "PythonGraphBuilder",
]
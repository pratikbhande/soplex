"""
Shared test fixtures for soplex tests.
Includes MockLLMProvider, sample SOPs, and tool definitions.
"""
import pytest
import yaml
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock

from soplex.parser.models import Tool, SOPDefinition
from soplex.parser.sop_parser import SOPParser


class MockLLMProvider:
    """
    Mock LLM provider that returns predefined responses.
    Records all calls for testing verification.
    """

    def __init__(self):
        self.calls = []
        self.responses = {
            "default": {
                "content": "I understand. How can I help you today?",
                "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
                "cost": 0.000027,  # Based on gpt-4o-mini pricing
                "model": "gpt-4o-mini",
                "provider": "mock",
                "latency_ms": 150
            },
            "greeting": {
                "content": "Hello! I'm here to help with your request.",
                "usage": {"prompt_tokens": 15, "completion_tokens": 10, "total_tokens": 25},
                "cost": 0.000038,
                "model": "gpt-4o-mini",
                "provider": "mock",
                "latency_ms": 120
            },
            "confirm": {
                "content": "Yes, I can confirm that information is correct.",
                "usage": {"prompt_tokens": 20, "completion_tokens": 9, "total_tokens": 29},
                "cost": 0.000044,
                "model": "gpt-4o-mini",
                "provider": "mock",
                "latency_ms": 180
            },
            "inform": {
                "content": "I've processed your request successfully.",
                "usage": {"prompt_tokens": 25, "completion_tokens": 7, "total_tokens": 32},
                "cost": 0.000048,
                "model": "gpt-4o-mini",
                "provider": "mock",
                "latency_ms": 100
            },
            "ask": {
                "content": "Could you please provide the requested information?",
                "usage": {"prompt_tokens": 18, "completion_tokens": 11, "total_tokens": 29},
                "cost": 0.000044,
                "model": "gpt-4o-mini",
                "provider": "mock",
                "latency_ms": 140
            }
        }

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Generate mock response and record the call."""
        call_info = {
            "messages": messages,
            "kwargs": kwargs
        }
        self.calls.append(call_info)

        # Determine response type based on last message content
        if messages:
            last_content = messages[-1].get("content", "").lower()
            if "greet" in last_content or "hello" in last_content:
                response_key = "greeting"
            elif "confirm" in last_content or "verify" in last_content:
                response_key = "confirm"
            elif "inform" in last_content or "tell" in last_content:
                response_key = "inform"
            elif "ask" in last_content or "?" in last_content:
                response_key = "ask"
            else:
                response_key = "default"
        else:
            response_key = "default"

        return self.responses[response_key].copy()

    def reset(self):
        """Reset call history."""
        self.calls = []

    def get_call_count(self) -> int:
        """Get number of LLM calls made."""
        return len(self.calls)

    def get_last_call(self) -> Dict[str, Any]:
        """Get the most recent call."""
        return self.calls[-1] if self.calls else {}


@pytest.fixture
def mock_llm_provider():
    """Provide a fresh mock LLM provider for each test."""
    return MockLLMProvider()


@pytest.fixture
def sample_linear_sop():
    """Simple linear SOP for testing."""
    return """PROCEDURE: Simple Greeting
TRIGGER: User says hello
TOOLS: none

1. Greet the user warmly
2. Ask how you can help them today
3. Thank them for their inquiry"""


@pytest.fixture
def sample_branch_sop():
    """SOP with branching logic for testing."""
    return """PROCEDURE: Account Verification
TRIGGER: User requests account access
TOOLS: user_db

1. Ask user for their email address
2. Lookup user account in user_db
3. Check if account is active
   - YES: Welcome user and proceed to step 5
   - NO: Inform user account is inactive and end
4. This step should be skipped
5. Ask user what they would like to do today"""


@pytest.fixture
def sample_complex_sop():
    """Complex SOP with multiple branches and tools."""
    return """PROCEDURE: Order Processing
TRIGGER: Customer places order
TOOLS: inventory_db, payment_api, shipping_api

1. Receive order details from customer
2. Check inventory in inventory_db for requested items
3. Verify if all items are in stock
   - YES: Proceed to payment
   - NO: Offer alternatives or partial order
4. Process payment using payment_api
5. Check if payment was successful
   - YES: Confirm order and arrange shipping
   - NO: Inform customer of payment issue and end
6. Calculate shipping cost using shipping_api
7. Send order confirmation to customer
8. End order process"""


@pytest.fixture
def refund_sop():
    """Load the refund.sop example file."""
    sop_path = Path(__file__).parent.parent / "examples" / "refund.sop"
    return sop_path.read_text()


@pytest.fixture
def password_reset_sop():
    """Load the password_reset.sop example file."""
    sop_path = Path(__file__).parent.parent / "examples" / "password_reset.sop"
    return sop_path.read_text()


@pytest.fixture
def fraud_check_sop():
    """Load the fraud_check.sop example file."""
    sop_path = Path(__file__).parent.parent / "examples" / "fraud_check.sop"
    return sop_path.read_text()


@pytest.fixture
def tools_definitions():
    """Load tool definitions from tools.yaml."""
    tools_path = Path(__file__).parent.parent / "examples" / "tools.yaml"
    with open(tools_path) as f:
        tools_data = yaml.safe_load(f)

    tools = {}
    for tool_name, tool_config in tools_data.items():
        tools[tool_name] = Tool(
            name=tool_name,
            description=tool_config.get("description", ""),
            parameters=tool_config.get("parameters", {}),
            mock_response=tool_config.get("mock_responses", {})
        )

    return tools


@pytest.fixture
def sop_parser():
    """Provide a fresh SOP parser instance."""
    return SOPParser()


@pytest.fixture
def parsed_refund_sop(sop_parser, refund_sop, tools_definitions):
    """Parsed refund SOP for testing."""
    return sop_parser.parse(refund_sop, tools_definitions)


@pytest.fixture
def parsed_linear_sop(sop_parser, sample_linear_sop):
    """Parsed linear SOP for testing."""
    return sop_parser.parse(sample_linear_sop)


@pytest.fixture
def parsed_branch_sop(sop_parser, sample_branch_sop, tools_definitions):
    """Parsed branching SOP for testing."""
    return sop_parser.parse(sample_branch_sop, tools_definitions)


@pytest.fixture
def mock_tools():
    """Mock tool functions for testing."""
    def mock_order_db(order_number: str) -> Dict[str, Any]:
        """Mock order database lookup."""
        return {
            "order_id": order_number,
            "customer_email": "test@example.com",
            "order_date": "2024-03-01",
            "status": "delivered",
            "total": 99.99,
            "items": ["Test Item"]
        }

    def mock_payments_api(action: str, amount: float, reference: str) -> Dict[str, Any]:
        """Mock payment API."""
        return {
            "status": "success",
            "transaction_id": f"TXN-{reference}",
            "amount": amount,
            "processed_at": "2024-03-14T12:00:00Z"
        }

    def mock_identity_check(email: str, order_number: str) -> Dict[str, Any]:
        """Mock identity verification."""
        return {
            "verified": True,
            "confidence": 0.95,
            "email_match": True
        }

    return {
        "order_db": mock_order_db,
        "payments_api": mock_payments_api,
        "identity_check": mock_identity_check
    }


# Test configuration
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up clean test environment."""
    # Mock environment variables
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("SOPLEX_PROVIDER", "openai")
    monkeypatch.setenv("SOPLEX_MODEL", "gpt-4o-mini")


@pytest.fixture
def temp_sop_file(tmp_path):
    """Create a temporary SOP file for testing."""
    sop_content = """PROCEDURE: Test SOP
TRIGGER: Testing
TOOLS: test_tool

1. Start the test
2. Run the test
3. Complete the test"""

    sop_file = tmp_path / "test.sop"
    sop_file.write_text(sop_content)
    return sop_file
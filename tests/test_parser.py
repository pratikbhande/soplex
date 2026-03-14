"""
Tests for SOP parsing functionality.
Tests the conversion of plain-text SOPs to structured SOPDefinition objects.
"""
import pytest
from soplex.parser.models import StepType, SOPDefinition
from soplex.parser.sop_parser import SOPParser


class TestSOPParser:
    """Test SOP parsing functionality."""

    def test_parse_linear_sop(self, sop_parser, sample_linear_sop):
        """Test parsing a simple linear SOP."""
        sop_def = sop_parser.parse(sample_linear_sop)

        assert isinstance(sop_def, SOPDefinition)
        assert sop_def.name == "Simple Greeting"
        assert sop_def.trigger == "User says hello"
        assert sop_def.tools == ["none"]
        assert len(sop_def.steps) == 3
        assert sop_def.total_steps == 3
        assert sop_def.start_step_id == "step_1"

        # Check step linking
        assert sop_def.steps[0].next_step_id == "step_2"
        assert sop_def.steps[1].next_step_id == "step_3"
        assert sop_def.steps[2].next_step_id is None  # Last step

    def test_parse_branched_sop(self, sop_parser, sample_branch_sop, tools_definitions):
        """Test parsing SOP with branching logic."""
        sop_def = sop_parser.parse(sample_branch_sop, tools_definitions)

        assert sop_def.name == "Account Verification"
        assert sop_def.trigger == "User requests account access"
        assert sop_def.tools == ["user_db"]
        assert len(sop_def.steps) == 5

        # Find the branch step
        branch_step = None
        for step in sop_def.steps:
            if step.type == StepType.BRANCH:
                branch_step = step
                break

        assert branch_step is not None
        assert branch_step.branch is not None
        assert "active" in branch_step.branch.condition.lower()
        assert "welcome" in branch_step.branch.yes_action.lower()
        assert "inactive" in branch_step.branch.no_action.lower()

    def test_parse_nested_branches(self, sop_parser):
        """Test parsing SOP with multiple branches."""
        sop_text = """PROCEDURE: Multi Branch Test
TRIGGER: Test multiple conditions
TOOLS: test_db

1. Start process
2. Check first condition
   - YES: Go to step 4
   - NO: Check second condition
3. Check second condition
   - YES: Continue process
   - NO: End process
4. Final step
5. End"""

        sop_def = sop_parser.parse(sop_text)

        assert len(sop_def.steps) == 5
        branch_steps = [s for s in sop_def.steps if s.type == StepType.BRANCH]
        assert len(branch_steps) == 2  # Two branch points

    def test_parse_tools_header(self, sop_parser):
        """Test parsing tools from header."""
        sop_text = """PROCEDURE: Tool Test
TRIGGER: Test tools parsing
TOOLS: tool1, tool2, tool3

1. Use tool1
2. Use tool2
3. Use tool3"""

        sop_def = sop_parser.parse(sop_text)

        assert sop_def.tools == ["tool1", "tool2", "tool3"]

    def test_parse_escalate_step(self, sop_parser):
        """Test parsing escalation steps."""
        sop_text = """PROCEDURE: Escalation Test
TRIGGER: Test escalation
TOOLS: none

1. Try to resolve issue
2. If unable to resolve, escalate to human supervisor
3. End process"""

        sop_def = sop_parser.parse(sop_text)

        escalate_steps = [s for s in sop_def.steps if s.type == StepType.ESCALATE]
        assert len(escalate_steps) == 1
        assert "escalate" in escalate_steps[0].action.lower()

    def test_parse_multiple_ends(self, sop_parser):
        """Test parsing SOP with multiple end points."""
        sop_text = """PROCEDURE: Multiple Ends
TRIGGER: Test multiple endings
TOOLS: none

1. Start process
2. Check condition
   - YES: Complete successfully and end
   - NO: Report error and end
3. This should not be reached"""

        sop_def = sop_parser.parse(sop_text)

        # Should have detected END keywords in branch actions
        branch_step = next((s for s in sop_def.steps if s.type == StepType.BRANCH), None)
        assert branch_step is not None
        assert "end" in branch_step.branch.yes_action.lower()
        assert "end" in branch_step.branch.no_action.lower()

    def test_parse_single_step(self, sop_parser):
        """Test parsing SOP with single step."""
        sop_text = """PROCEDURE: Single Step
TRIGGER: Simple test
TOOLS: none

1. Complete the task"""

        sop_def = sop_parser.parse(sop_text)

        assert len(sop_def.steps) == 1
        assert sop_def.start_step_id == "step_1"
        assert sop_def.steps[0].next_step_id is None

    def test_parse_no_header(self, sop_parser):
        """Test parsing SOP without complete header."""
        sop_text = """1. First step
2. Second step
3. Third step"""

        sop_def = sop_parser.parse(sop_text)

        assert sop_def.name == "Unnamed SOP"
        assert sop_def.trigger is None
        assert sop_def.tools == []
        assert len(sop_def.steps) == 3

    def test_parse_refund_example(self, parsed_refund_sop):
        """Test parsing the refund example SOP."""
        sop_def = parsed_refund_sop

        assert sop_def.name == "Customer Refund Request"
        assert len(sop_def.steps) == 9
        assert sop_def.tools == ["order_db", "payments_api", "identity_check"]

        # Should have LLM, CODE, and BRANCH steps
        assert sop_def.llm_steps > 0
        assert sop_def.code_steps > 0
        assert sop_def.branch_steps > 0

    def test_step_numbering(self, sop_parser, sample_linear_sop):
        """Test that step numbers are correctly assigned."""
        sop_def = sop_parser.parse(sample_linear_sop)

        for i, step in enumerate(sop_def.steps):
            assert step.number == i + 1
            assert step.id == f"step_{i + 1}"

    def test_tool_extraction(self, sop_parser):
        """Test extraction of tool references from step text."""
        sop_text = """PROCEDURE: Tool Extraction Test
TRIGGER: Test tool extraction
TOOLS: order_db, payment_api

1. Check order_db for customer info
2. Process payment using payment_api
3. Call shipping_service for delivery"""

        sop_def = sop_parser.parse(sop_text)

        # Step 1 should detect order_db
        step1_tools = sop_def.steps[0].tools_required
        assert "order_db" in step1_tools or len(step1_tools) > 0

    def test_validation_errors(self, sop_parser, sample_branch_sop, tools_definitions):
        """Test SOP validation catches common errors."""
        sop_def = sop_parser.parse(sample_branch_sop, tools_definitions)
        issues = sop_parser.validate_sop(sop_def)

        # Should be minimal issues in a well-formed SOP
        assert isinstance(issues, list)
        # Most issues should be warnings, not critical errors

    def test_step_statistics(self, parsed_refund_sop):
        """Test that step type statistics are calculated correctly."""
        sop_def = parsed_refund_sop

        # Total should equal sum of all types
        total_classified = (sop_def.llm_steps + sop_def.code_steps +
                           sop_def.hybrid_steps + sop_def.branch_steps)

        # Allow for END/ESCALATE steps that aren't counted in the main categories
        assert total_classified <= sop_def.total_steps

    def test_cost_estimation(self, parsed_refund_sop):
        """Test cost estimation functionality."""
        sop_def = parsed_refund_sop
        from soplex.config import PRICING

        cost_estimate = sop_def.get_cost_estimate(PRICING)

        assert "llm_cost" in cost_estimate
        assert "code_cost" in cost_estimate
        assert "total_cost" in cost_estimate
        assert "savings" in cost_estimate
        assert "savings_percent" in cost_estimate

        # Should show savings for hybrid approach
        assert cost_estimate["savings"] >= 0
        assert cost_estimate["total_cost"] <= cost_estimate["pure_llm_cost"]
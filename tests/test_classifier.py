"""
Tests for step classification functionality.
Tests the keyword-based classification of SOP steps into execution types.
"""
import pytest
from soplex.parser.step_classifier import StepClassifier
from soplex.parser.models import StepType


class TestStepClassifier:
    """Test step classification functionality."""

    def test_llm_keywords(self):
        """Test classification of LLM/conversational steps."""
        test_cases = [
            "Greet the customer warmly",
            "Ask the user for their email address",
            "Inform the customer about the policy",
            "Confirm with the user that they understand",
            "Explain the refund process to the customer",
            "Thank the customer for their patience",
            "Apologize for the inconvenience caused",
            "Welcome the user to our service",
        ]

        for step_text in test_cases:
            step_type, keywords, confidence = StepClassifier.classify_step(step_text, 1)
            assert step_type == StepType.LLM, f"'{step_text}' should be classified as LLM"
            assert confidence > 0.5, f"Low confidence for LLM step: {confidence}"

    def test_code_keywords(self):
        """Test classification of CODE/deterministic steps."""
        test_cases = [
            "Check if the order was placed within 30 days",
            "Lookup user details in the database",
            "Calculate the refund amount",
            "Fetch order information from order_db",
            "Verify the customer's identity",
            "Query the payment system for transaction details",
            "Process the payment using the API",
            "Update the order status to completed",
            "Send notification to the shipping service",
        ]

        for step_text in test_cases:
            step_type, keywords, confidence = StepClassifier.classify_step(step_text, 1)
            assert step_type == StepType.CODE, f"'{step_text}' should be classified as CODE"
            assert confidence > 0.5, f"Low confidence for CODE step: {confidence}"

    def test_branch_keywords(self):
        """Test classification of BRANCH/conditional steps."""
        test_cases = [
            "Check if the account is active",
            "Verify whether the payment was successful",
            "Determine if the user is authorized",
            "If the amount is over $100, require approval",
            "When the order status is delivered, proceed",
            "Check: Is the customer a premium member?",
        ]

        for step_text in test_cases:
            step_type, keywords, confidence = StepClassifier.classify_step(step_text, 1)
            assert step_type in [StepType.BRANCH, StepType.CODE], \
                f"'{step_text}' should be classified as BRANCH or CODE"

    def test_escalate_keywords(self):
        """Test classification of ESCALATE steps."""
        test_cases = [
            "Escalate to supervisor for approval",
            "Hand off to human agent for complex handling",
            "Transfer to human support representative",
            "Flag for manual review by security team",
            "Contact manager for authorization",
        ]

        for step_text in test_cases:
            step_type, keywords, confidence = StepClassifier.classify_step(step_text, 1)
            assert step_type == StepType.ESCALATE, f"'{step_text}' should be classified as ESCALATE"
            assert confidence >= 0.9, f"Should have high confidence for escalate: {confidence}"

    def test_end_keywords(self):
        """Test classification of END steps."""
        test_cases = [
            "End the process successfully",
            "Complete the transaction and finish",
            "Close the support case",
            "Done processing the request",
            "Finalize the order and terminate",
        ]

        for step_text in test_cases:
            step_type, keywords, confidence = StepClassifier.classify_step(step_text, 1)
            assert step_type == StepType.END, f"'{step_text}' should be classified as END"
            assert confidence >= 0.9, f"Should have high confidence for end: {confidence}"

    def test_comparison_patterns(self):
        """Test classification of steps with comparison patterns (always CODE)."""
        test_cases = [
            "Check if amount is above $500",
            "Verify the transaction is below €1000",
            "Confirm the order is over £200",
            "Check if payment is under ¥50000",
            "Verify completion within 24 hours",
            "Check if account is active",
            "Confirm the status is expired",
            "Verify the user is locked",
        ]

        for step_text in test_cases:
            step_type, keywords, confidence = StepClassifier.classify_step(step_text, 1)
            assert step_type == StepType.CODE, f"'{step_text}' should be classified as CODE (comparison)"
            assert confidence >= 0.9, f"Should have high confidence for comparison: {confidence}"

    def test_hybrid_classification(self):
        """Test classification of HYBRID steps (LLM + CODE)."""
        test_cases = [
            "Ask the customer for order number and verify it in the database",
            "Greet the user and check their account status",
            "Confirm the payment details and process the transaction",
            "Inform customer about the issue and update their record",
        ]

        for step_text in test_cases:
            step_type, keywords, confidence = StepClassifier.classify_step(step_text, 1)
            assert step_type == StepType.HYBRID, f"'{step_text}' should be classified as HYBRID"
            assert confidence > 0.5, f"Low confidence for hybrid step: {confidence}"

    def test_ambiguous_defaults_to_llm(self):
        """Test that ambiguous steps default to LLM."""
        ambiguous_cases = [
            "Handle the customer request appropriately",
            "Process this information",
            "Take the next action",
            "Continue with the workflow",
        ]

        for step_text in ambiguous_cases:
            step_type, keywords, confidence = StepClassifier.classify_step(step_text, 1)
            assert step_type == StepType.LLM, f"'{step_text}' should default to LLM"
            assert confidence <= 0.6, f"Should have low confidence for ambiguous: {confidence}"

    def test_check_colon_pattern(self):
        """Test that 'CHECK:' pattern always results in BRANCH."""
        test_cases = [
            "CHECK: Is the user authenticated?",
            "Check: Does the account have sufficient funds?",
            "3. CHECK: Has the payment been processed?",
        ]

        for step_text in test_cases:
            step_type, keywords, confidence = StepClassifier.classify_step(step_text, 1)
            assert step_type == StepType.BRANCH, f"'{step_text}' with CHECK: should be BRANCH"
            assert confidence >= 0.9, f"Should have high confidence for CHECK: pattern"

    def test_classification_summary(self):
        """Test classification summary statistics."""
        test_steps = [
            "Greet the customer",  # LLM
            "Check order in database",  # CODE
            "Ask for confirmation",  # LLM
            "Process payment",  # CODE
            "Check: Is payment successful?",  # BRANCH
            "End the process",  # END
        ]

        classifications = StepClassifier.classify_steps(test_steps)
        summary = StepClassifier.get_classification_summary(classifications)

        assert summary["total_steps"] == 6
        assert StepType.LLM in summary["type_counts"]
        assert StepType.CODE in summary["type_counts"]
        assert StepType.BRANCH in summary["type_counts"]
        assert StepType.END in summary["type_counts"]
        assert summary["average_confidence"] > 0

    def test_explain_classification(self):
        """Test detailed classification explanation."""
        step_text = "Greet the customer and verify their account status"

        explanation = StepClassifier.explain_classification(step_text)

        assert explanation["step_text"] == step_text
        assert "classified_as" in explanation
        assert "confidence" in explanation
        assert "keywords_found" in explanation
        assert "analysis" in explanation
        assert "reasoning" in explanation

        # Should detect both LLM and CODE keywords
        analysis = explanation["analysis"]
        assert len(analysis["llm_keywords"]) > 0  # "greet"
        assert len(analysis["code_keywords"]) > 0  # "verify"

    def test_edge_cases(self):
        """Test edge cases and special patterns."""
        edge_cases = [
            ("", StepType.LLM),  # Empty string
            ("1. ", StepType.LLM),  # Just step number
            ("Process the user's request immediately", StepType.CODE),  # Multiple keywords
            ("Ask user to confirm and then process payment", StepType.HYBRID),  # Clear hybrid
        ]

        for step_text, expected_type in edge_cases:
            step_type, keywords, confidence = StepClassifier.classify_step(step_text, 1)
            assert step_type == expected_type, f"'{step_text}' should be {expected_type.value}"

    def test_confidence_scoring(self):
        """Test that confidence scores are reasonable."""
        # High confidence cases
        high_confidence_cases = [
            "END the process completely",  # Clear END
            "ESCALATE to human supervisor",  # Clear ESCALATE
            "CHECK: Is amount above $500?",  # Clear BRANCH with pattern
        ]

        for step_text in high_confidence_cases:
            step_type, keywords, confidence = StepClassifier.classify_step(step_text, 1)
            assert confidence >= 0.9, f"Should have high confidence for: '{step_text}'"

        # Low confidence cases
        low_confidence_cases = [
            "Handle this situation",  # Ambiguous
            "Do the needful",  # Very ambiguous
        ]

        for step_text in low_confidence_cases:
            step_type, keywords, confidence = StepClassifier.classify_step(step_text, 1)
            assert confidence <= 0.6, f"Should have low confidence for: '{step_text}'"

    def test_keyword_tracking(self):
        """Test that found keywords are properly tracked."""
        step_text = "Ask the customer and then check the database"

        step_type, keywords, confidence = StepClassifier.classify_step(step_text, 1)

        assert step_type == StepType.HYBRID
        # Should track both LLM and CODE keywords
        llm_keywords = [k for k in keywords if k.startswith("llm:")]
        code_keywords = [k for k in keywords if k.startswith("code:")]

        assert len(llm_keywords) > 0, "Should find LLM keywords"
        assert len(code_keywords) > 0, "Should find CODE keywords"
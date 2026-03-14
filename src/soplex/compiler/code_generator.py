"""
Code generator for soplex.
Generates Python functions for CODE and BRANCH steps to enable deterministic execution.
"""
import re
from typing import Dict, List, Optional, Any, Tuple
from ..parser.models import Step, StepType, BranchCondition


class CodeGenerator:
    """
    Generates executable Python code for deterministic SOP steps.
    Converts step actions into function calls and conditional logic.
    """

    def __init__(self):
        self.generated_functions: Dict[str, str] = {}

    def generate_step_handler(self, step: Step) -> str:
        """
        Generate a Python function for a step.

        Args:
            step: Step to generate handler for

        Returns:
            Generated Python function code
        """
        if step.type == StepType.CODE:
            return self._generate_code_handler(step)
        elif step.type == StepType.BRANCH:
            return self._generate_branch_handler(step)
        elif step.type == StepType.HYBRID:
            return self._generate_hybrid_handler(step)
        else:
            # LLM, END, ESCALATE steps don't need generated code
            return ""

    def _generate_code_handler(self, step: Step) -> str:
        """Generate handler for CODE step."""
        func_name = f"handle_{step.id}"

        # Parse the action to determine what to do
        action_lower = step.action.lower()
        tools = step.tools_required

        # Generate function body based on action keywords
        body_lines = []

        if any(keyword in action_lower for keyword in ["lookup", "fetch", "retrieve", "get"]):
            # Database/API lookup operation
            if tools:
                tool_name = tools[0]
                body_lines.extend([
                    f'    # Lookup operation using {tool_name}',
                    f'    tool_func = tools.get("{tool_name}")',
                    '    if not tool_func:',
                    f'        raise ValueError("Tool {tool_name} not available")',
                    '',
                    '    # Extract parameters from state or user input',
                    '    params = state.get("step_params", {})',
                    '    result = tool_func(**params)',
                    '',
                    '    # Store result in state',
                    '    state["lookup_result"] = result',
                    '    state["last_tool_result"] = result',
                    '',
                    '    return {"status": "success", "result": result}',
                ])
            else:
                body_lines.extend([
                    '    # Generic lookup operation',
                    '    params = state.get("step_params", {})',
                    '    # TODO: Implement actual lookup logic',
                    '    result = {"status": "completed"}',
                    '    state["lookup_result"] = result',
                    '    return {"status": "success", "result": result}',
                ])

        elif any(keyword in action_lower for keyword in ["calculate", "compute"]):
            # Calculation operation
            body_lines.extend([
                '    # Calculation operation',
                '    data = state.get("data", {})',
                '    ',
                '    # Extract numeric values for calculation',
                '    # TODO: Implement specific calculation logic based on step action',
                '    if "refund" in step.action.lower():',
                '        order_total = data.get("order_total", 0)',
                '        shipping = data.get("shipping", 0)',
                '        refund_amount = order_total - shipping if shipping > 0 else order_total',
                '        result = {"refund_amount": refund_amount}',
                '    else:',
                '        result = {"calculated_value": 42}  # Placeholder',
                '',
                '    state["calculation_result"] = result',
                '    return {"status": "success", "result": result}',
            ])

        elif any(keyword in action_lower for keyword in ["process", "execute", "run"]):
            # Processing operation
            if tools:
                tool_name = tools[0]
                body_lines.extend([
                    f'    # Processing operation using {tool_name}',
                    f'    tool_func = tools.get("{tool_name}")',
                    '    if not tool_func:',
                    f'        raise ValueError("Tool {tool_name} not available")',
                    '',
                    '    # Get data from previous steps',
                    '    data = state.get("data", {})',
                    '    params = state.get("step_params", data)',
                    '',
                    '    result = tool_func(**params)',
                    '    state["processing_result"] = result',
                    '',
                    '    return {"status": "success", "result": result}',
                ])
            else:
                body_lines.extend([
                    '    # Generic processing operation',
                    '    data = state.get("data", {})',
                    '    # TODO: Implement actual processing logic',
                    '    result = {"status": "processed"}',
                    '    state["processing_result"] = result',
                    '    return {"status": "success", "result": result}',
                ])

        elif any(keyword in action_lower for keyword in ["verify", "validate", "check"]):
            # Verification operation
            body_lines.extend([
                '    # Verification operation',
                '    data = state.get("data", {})',
                '    params = state.get("step_params", {})',
                '',
                '    # TODO: Implement specific verification logic',
                '    is_valid = True  # Placeholder verification result',
                '',
                '    result = {"is_valid": is_valid, "verification": "completed"}',
                '    state["verification_result"] = result',
                '',
                '    return {"status": "success", "result": result, "is_valid": is_valid}',
            ])

        else:
            # Generic CODE step
            body_lines.extend([
                '    # Generic code execution',
                '    data = state.get("data", {})',
                '    params = state.get("step_params", {})',
                '',
                '    # Execute step action',
                f'    # Action: {step.action}',
                '    result = {"status": "completed", "action": step.action}',
                '',
                '    state["step_result"] = result',
                '    return {"status": "success", "result": result}',
            ])

        # Build complete function
        function_code = f'''def {func_name}(state, tools, step):
    """
    Generated handler for step {step.number}: {step.action}
    Type: {step.type.value.upper()}
    """
{chr(10).join(body_lines)}'''

        return function_code

    def _generate_branch_handler(self, step: Step) -> str:
        """Generate handler for BRANCH step."""
        func_name = f"handle_{step.id}"

        # Handle case where step is classified as BRANCH but no explicit branch object
        if not step.branch:
            condition = step.action  # Use the action itself as the condition
        else:
            condition = step.branch.condition

        # Parse condition to generate appropriate logic
        body_lines = self._generate_condition_logic(condition, step)

        # Ensure body_lines is a list
        if body_lines is None:
            body_lines = [
                '    # Fallback condition handler',
                '    result = True',
                '    state["last_condition_result"] = result',
                '    return {"status": "success", "result": result, "condition_met": result}',
            ]

        function_code = f'''def {func_name}(state, tools, step):
    """
    Generated handler for branch step {step.number}: {condition}
    Type: BRANCH
    """
{chr(10).join(body_lines)}'''

        return function_code

    def _generate_condition_logic(self, condition: str, step: Step) -> List[str]:
        """Generate logic for evaluating branch conditions."""
        condition_lower = condition.lower()

        # Time-based conditions
        if "within" in condition_lower and "days" in condition_lower:
            days_match = re.search(r'within\s+(\d+)\s+days?', condition_lower)
            if days_match:
                days = days_match.group(1)
                return [
                    '    # Check time-based condition',
                    '    from datetime import datetime, timedelta',
                    '    ',
                    '    data = state.get("data", {})',
                    '    order_date_str = data.get("order_date")',
                    '    ',
                    '    if not order_date_str:',
                    '        result = False',
                    '    else:',
                    '        try:',
                    '            # Parse order date (assuming YYYY-MM-DD format)',
                    '            order_date = datetime.strptime(order_date_str, "%Y-%m-%d")',
                    '            now = datetime.now()',
                    f'            cutoff_date = now - timedelta(days={days})',
                    '            result = order_date >= cutoff_date',
                    '        except ValueError:',
                    '            result = False',
                    '    ',
                    '    state["last_condition_result"] = result',
                    '    return {"status": "success", "result": result, "condition_met": result}',
                ]

        # Status-based conditions
        elif "status" in condition_lower:
            status_patterns = [
                ("delivered", ["delivered", "completed"]),
                ("active", ["active", "enabled"]),
                ("locked", ["locked", "disabled", "suspended"]),
                ("successful", ["success", "successful", "completed"]),
            ]

            for status_key, status_values in status_patterns:
                if any(val in condition_lower for val in status_values):
                    return [
                        '    # Check status condition',
                        '    data = state.get("data", {})',
                        '    status = data.get("status", "").lower()',
                        '    ',
                        f'    # Check if status matches: {status_values}',
                        f'    expected_statuses = {status_values}',
                        '    result = status in expected_statuses',
                        '    ',
                        '    state["last_condition_result"] = result',
                        '    return {"status": "success", "result": result, "condition_met": result}',
                    ]

        # Amount-based conditions
        elif any(word in condition_lower for word in ["above", "below", "over", "under"]):
            amount_match = re.search(r'(above|below|over|under)\s*[£$€¥]?(\d+(?:\.\d+)?)', condition_lower)
            if amount_match:
                operator = amount_match.group(1)
                threshold = amount_match.group(2)
                comparison = ">" if operator in ["above", "over"] else "<"

                return [
                    '    # Check amount-based condition',
                    '    data = state.get("data", {})',
                    '    amount = data.get("amount", 0)',
                    '    if isinstance(amount, str):',
                    '        try:',
                    '            amount = float(amount)',
                    '        except ValueError:',
                    '            amount = 0',
                    '    ',
                    f'    result = amount {comparison} {threshold}',
                    '    ',
                    '    state["last_condition_result"] = result',
                    '    return {"status": "success", "result": result, "condition_met": result}',
                ]

        # Existence checks
        elif any(word in condition_lower for word in ["exists", "found", "available"]):
            return [
                '    # Check existence condition',
                '    data = state.get("data", {})',
                '    lookup_result = state.get("lookup_result")',
                '    ',
                '    # Check if previous lookup found results',
                '    if lookup_result:',
                '        result = lookup_result.get("found", True)',
                '        if isinstance(lookup_result, dict) and "error" not in lookup_result:',
                '            result = True',
                '        elif isinstance(lookup_result, list):',
                '            result = len(lookup_result) > 0',
                '        else:',
                '            result = bool(lookup_result)',
                '    else:',
                '        result = False',
                '    ',
                '    state["last_condition_result"] = result',
                '    return {"status": "success", "result": result, "condition_met": result}',
            ]

        # Generic condition (always returns True for now)
        else:
            return [
                '    # Generic condition evaluation',
                f'    # Condition: {condition}',
                '    ',
                '    data = state.get("data", {})',
                '    # TODO: Implement specific condition logic',
                '    result = True  # Placeholder - always true for now',
                '    ',
                '    state["last_condition_result"] = result',
                '    return {"status": "success", "result": result, "condition_met": result}',
            ]

    def _generate_hybrid_handler(self, step: Step) -> str:
        """Generate handler for HYBRID step (LLM + validation)."""
        func_name = f"handle_{step.id}"

        return f'''def {func_name}(state, tools, step):
    """
    Generated handler for hybrid step {step.number}: {step.action}
    Type: HYBRID (LLM + Code validation)
    """
    # HYBRID steps require both LLM interaction and code validation
    # The LLM part will be handled by the executor
    # This function handles the validation/code part

    data = state.get("data", {{}})
    llm_response = state.get("last_llm_response", "")

    # Validate LLM response using code logic
    # TODO: Implement specific validation logic for this hybrid step
    validation_result = {{
        "is_valid": True,
        "validation_notes": "LLM response validated",
        "llm_response": llm_response
    }}

    state["hybrid_validation"] = validation_result
    return {{"status": "success", "result": validation_result}}'''

    def generate_all_handlers(self, steps: List[Step]) -> Dict[str, str]:
        """
        Generate handlers for all steps that require code generation.

        Args:
            steps: List of steps to generate handlers for

        Returns:
            Dictionary mapping step IDs to generated function code
        """
        handlers = {}

        for step in steps:
            if step.type in [StepType.CODE, StepType.BRANCH, StepType.HYBRID]:
                handler_code = self.generate_step_handler(step)
                if handler_code:
                    handlers[step.id] = handler_code

        return handlers

    def compile_handlers_module(self, handlers: Dict[str, str]) -> str:
        """
        Compile all handlers into a single Python module.

        Args:
            handlers: Dictionary of step ID to function code

        Returns:
            Complete Python module code
        """
        module_lines = [
            '"""',
            'Generated handlers for soplex SOP execution.',
            'This module contains compiled step handlers for deterministic execution.',
            '"""',
            '',
            'from typing import Dict, Any',
            'from datetime import datetime, timedelta',
            '',
            '# Generated step handlers',
            '',
        ]

        # Add all handler functions
        for step_id, handler_code in handlers.items():
            module_lines.append(handler_code)
            module_lines.append('')
            module_lines.append('')

        # Add handler registry
        module_lines.extend([
            '# Handler registry',
            'STEP_HANDLERS = {',
        ])

        for step_id in handlers.keys():
            func_name = f"handle_{step_id}"
            module_lines.append(f'    "{step_id}": {func_name},')

        module_lines.extend([
            '}',
            '',
            '',
            'def get_handler(step_id: str):',
            '    """Get handler function for a step."""',
            '    return STEP_HANDLERS.get(step_id)',
        ])

        return '\n'.join(module_lines)
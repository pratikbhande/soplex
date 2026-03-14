"""
SOP Parser for soplex.
Converts plain-text SOPs to structured SOPDefinition objects.
Handles flexible format with PROCEDURE/TRIGGER/TOOLS headers and numbered steps.
"""
import re
from typing import List, Dict, Optional, Tuple
from .models import SOPDefinition, Step, StepType, BranchCondition, Tool
from .step_classifier import StepClassifier


class SOPParser:
    """
    Parser for plain-text Standard Operating Procedures.
    Converts flexible text format to structured SOPDefinition.
    """

    def __init__(self):
        self.classifier = StepClassifier()

    def parse(self, sop_text: str, tools_definitions: Optional[Dict[str, Tool]] = None) -> SOPDefinition:
        """
        Parse plain-text SOP into structured SOPDefinition.

        Args:
            sop_text: Raw SOP text
            tools_definitions: Optional tool definitions

        Returns:
            Structured SOPDefinition object
        """
        lines = sop_text.strip().split('\n')

        # Parse header information
        name, trigger, tools = self._parse_header(lines)

        # Extract step lines
        step_lines = self._extract_step_lines(lines)

        # Parse individual steps
        steps = self._parse_steps(step_lines)

        # Link steps and resolve branches
        self._link_steps(steps)

        # Determine start step
        start_step_id = steps[0].id if steps else None

        # Create SOPDefinition
        sop_def = SOPDefinition(
            name=name,
            trigger=trigger,
            tools=tools,
            steps=steps,
            tool_definitions=tools_definitions or {},
            source_text=sop_text,
            start_step_id=start_step_id
        )

        return sop_def

    def _parse_header(self, lines: List[str]) -> Tuple[str, Optional[str], List[str]]:
        """
        Parse header information from SOP lines.

        Returns:
            Tuple of (name, trigger, tools_list)
        """
        name = "Unnamed SOP"
        trigger = None
        tools = []

        for line in lines:
            line = line.strip()

            # Parse PROCEDURE
            if line.upper().startswith('PROCEDURE:'):
                name = line.split(':', 1)[1].strip()

            # Parse TRIGGER
            elif line.upper().startswith('TRIGGER:'):
                trigger = line.split(':', 1)[1].strip()

            # Parse TOOLS
            elif line.upper().startswith('TOOLS:'):
                tools_text = line.split(':', 1)[1].strip()
                if tools_text:
                    # Split by comma and clean up
                    tools = [tool.strip() for tool in tools_text.split(',') if tool.strip()]

        return name, trigger, tools

    def _extract_step_lines(self, lines: List[str]) -> List[str]:
        """
        Extract numbered step lines from the SOP text.
        Supports various numbering formats: "1.", "1)", "1 -", etc.
        """
        step_lines = []
        current_step = ""
        in_step = False

        for line in lines:
            line = line.strip()

            # Skip empty lines and header lines
            if not line or any(line.upper().startswith(header)
                              for header in ['PROCEDURE:', 'TRIGGER:', 'TOOLS:']):
                continue

            # Check if this is a new step (numbered line)
            if re.match(r'^\d+[\.\)\-\:]?\s+', line):
                # Save previous step if exists
                if current_step and in_step:
                    step_lines.append(current_step.strip())

                # Start new step
                current_step = line
                in_step = True

            # Check for sub-items (YES/NO branches)
            elif re.match(r'^\s*-\s*(YES|NO|yes|no):', line):
                if in_step:
                    current_step += "\n" + line

            # Continuation of current step
            elif in_step and (line.startswith(' ') or line.startswith('\t')):
                current_step += "\n" + line

            # If we find a non-step line after being in a step, end the step
            elif in_step:
                step_lines.append(current_step.strip())
                current_step = ""
                in_step = False

        # Don't forget the last step
        if current_step and in_step:
            step_lines.append(current_step.strip())

        return step_lines

    def _parse_steps(self, step_lines: List[str]) -> List[Step]:
        """
        Parse individual step lines into Step objects.
        Handles branching logic (CHECK/YES/NO patterns).
        """
        steps = []

        for i, step_line in enumerate(step_lines):
            step_number = i + 1
            step_id = f"step_{step_number}"

            # Check if this is a branching step
            if self._is_branch_step(step_line):
                step = self._parse_branch_step(step_line, step_id, step_number)
            else:
                step = self._parse_regular_step(step_line, step_id, step_number)

            steps.append(step)

        return steps

    def _is_branch_step(self, step_line: str) -> bool:
        """Check if a step contains branching logic (YES/NO patterns)."""
        return ('YES:' in step_line.upper() or 'NO:' in step_line.upper() or
                'CHECK:' in step_line.upper())

    def _parse_branch_step(self, step_line: str, step_id: str, step_number: int) -> Step:
        """Parse a step with branching logic."""
        lines = step_line.split('\n')
        main_line = lines[0].strip()

        # Extract step number and main action
        match = re.match(r'^\d+[\.\)\-\:]?\s+(.+)', main_line)
        action = match.group(1) if match else main_line

        # Initialize branch condition
        yes_action = ""
        no_action = ""

        # Parse YES/NO lines
        for line in lines[1:]:
            line = line.strip()
            if line.upper().startswith('- YES:') or line.upper().startswith('-YES:'):
                yes_action = line.split(':', 1)[1].strip()
            elif line.upper().startswith('- NO:') or line.upper().startswith('-NO:'):
                no_action = line.split(':', 1)[1].strip()

        # Create branch condition
        branch = BranchCondition(
            condition=action,
            yes_action=yes_action,
            no_action=no_action
        )

        # Classify the step
        step_type, keywords, confidence = self.classifier.classify_step(step_line, step_number)

        # Force BRANCH type if we detected branching
        if step_type != StepType.BRANCH:
            step_type = StepType.BRANCH
            confidence = max(confidence, 0.9)

        return Step(
            id=step_id,
            number=step_number,
            text=step_line,
            type=step_type,
            action=action,
            branch=branch,
            confidence=confidence,
            keywords=keywords
        )

    def _parse_regular_step(self, step_line: str, step_id: str, step_number: int) -> Step:
        """Parse a regular (non-branching) step."""
        # Extract step number and action
        match = re.match(r'^\d+[\.\)\-\:]?\s+(.+)', step_line)
        action = match.group(1) if match else step_line

        # Clean up action text
        action = re.sub(r'\s+', ' ', action.strip())

        # Classify the step
        step_type, keywords, confidence = self.classifier.classify_step(step_line, step_number)

        # Extract tool requirements
        tools_required = self._extract_tools_from_step(action)

        return Step(
            id=step_id,
            number=step_number,
            text=step_line,
            type=step_type,
            action=action,
            tools_required=tools_required,
            confidence=confidence,
            keywords=keywords
        )

    def _extract_tools_from_step(self, action: str) -> List[str]:
        """
        Extract tool names mentioned in the step action.
        Looks for common patterns like "check user_db", "call payments_api", etc.
        """
        tools = []
        action_lower = action.lower()

        # Common tool patterns
        tool_patterns = [
            r'check\s+(\w+_(?:db|database|api|service))',
            r'call\s+(\w+_(?:api|service|endpoint))',
            r'query\s+(\w+_(?:db|database))',
            r'lookup\s+(\w+_(?:db|database|table))',
            r'fetch\s+from\s+(\w+)',
            r'send\s+to\s+(\w+)',
            r'use\s+(\w+_(?:api|service))',
        ]

        for pattern in tool_patterns:
            matches = re.findall(pattern, action_lower)
            tools.extend(matches)

        return list(set(tools))  # Remove duplicates

    def _link_steps(self, steps: List[Step]) -> None:
        """
        Link steps together by setting next_step_id fields.
        Handle branching logic for BRANCH steps.
        """
        for i, step in enumerate(steps):
            # For regular steps, link to next step
            if step.type != StepType.BRANCH and step.type != StepType.END and step.type != StepType.ESCALATE:
                if i + 1 < len(steps):
                    step.next_step_id = steps[i + 1].id

            # For BRANCH steps, we'll resolve the YES/NO targets later in the compiler
            # This is because the targets might reference step numbers that need translation
            elif step.type == StepType.BRANCH and step.branch:
                # Try to resolve simple numeric references
                yes_action = step.branch.yes_action
                no_action = step.branch.no_action

                # Look for "go to step X" patterns
                yes_step = self._extract_step_reference(yes_action, steps)
                no_step = self._extract_step_reference(no_action, steps)

                if yes_step:
                    step.branch.yes_step_id = yes_step.id
                if no_step:
                    step.branch.no_step_id = no_step.id

    def _extract_step_reference(self, action: str, steps: List[Step]) -> Optional[Step]:
        """
        Extract step references from action text.
        Handles patterns like "go to step 5", "proceed to step 3", "end", etc.
        """
        action_lower = action.lower().strip()

        # Check for end/complete patterns
        if any(keyword in action_lower for keyword in ['end', 'complete', 'done', 'finish']):
            # Look for an END step
            for step in steps:
                if step.type == StepType.END:
                    return step

        # Check for numeric step references
        step_match = re.search(r'step\s+(\d+)', action_lower)
        if step_match:
            step_num = int(step_match.group(1))
            # Find step with that number
            for step in steps:
                if step.number == step_num:
                    return step

        return None

    def validate_sop(self, sop_def: SOPDefinition) -> List[str]:
        """
        Validate a parsed SOP for common issues.
        Returns list of warning/error messages.
        """
        issues = []

        # Check for orphaned steps
        referenced_steps = set()
        for step in sop_def.steps:
            if step.next_step_id:
                referenced_steps.add(step.next_step_id)
            if step.branch:
                if step.branch.yes_step_id:
                    referenced_steps.add(step.branch.yes_step_id)
                if step.branch.no_step_id:
                    referenced_steps.add(step.branch.no_step_id)

        step_ids = {step.id for step in sop_def.steps}
        unreferenced = step_ids - referenced_steps - {sop_def.start_step_id}
        if unreferenced and len(sop_def.steps) > 1:
            issues.append(f"Unreferenced steps: {', '.join(unreferenced)}")

        # Check for invalid references
        invalid_refs = referenced_steps - step_ids
        if invalid_refs:
            issues.append(f"Invalid step references: {', '.join(invalid_refs)}")

        # Check for missing tools
        required_tools = set()
        for step in sop_def.steps:
            required_tools.update(step.tools_required)

        available_tools = set(sop_def.tools) | set(sop_def.tool_definitions.keys())
        missing_tools = required_tools - available_tools
        if missing_tools:
            issues.append(f"Missing tool definitions: {', '.join(missing_tools)}")

        # Check for branch steps without complete branches
        for step in sop_def.steps:
            if step.type == StepType.BRANCH and step.branch:
                if not step.branch.yes_action or not step.branch.no_action:
                    issues.append(f"Step {step.number}: Incomplete branch (missing YES or NO)")

        return issues
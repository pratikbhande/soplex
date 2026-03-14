"""
Step classification engine for soplex.
Determines execution type (LLM/CODE/HYBRID/BRANCH/END/ESCALATE) based on keywords.
NO LLM calls - pure keyword-based classification for deterministic results.
"""
import re
from typing import List, Tuple
from .models import StepType


class StepClassifier:
    """
    Keyword-based step classifier.
    Classifies SOP steps without LLM calls for deterministic, fast results.
    """

    # Keywords that indicate CODE execution (deterministic logic)
    CODE_KEYWORDS = {
        "check", "lookup", "call", "fetch", "calculate", "compare", "query",
        "compute", "count", "send", "retrieve", "update", "delete",
        "validate", "verify", "search", "find", "get", "set", "store", "save",
        "load", "read", "write", "execute", "run", "perform", "trigger",
        "invoke", "submit", "post", "put", "patch", "remove", "create",
        "generate", "parse", "format", "transform", "convert", "filter"
    }

    # Context-specific CODE patterns (only match with specific context)
    CODE_CONTEXT_PATTERNS = [
        r'\bprocess\s+(?:payment|refund|order|transaction|data)\b',
        r'\bprocess\s+the\s+(?:payment|refund|order|transaction)\b',
    ]

    # Keywords that indicate LLM execution (conversational)
    LLM_KEYWORDS = {
        "ask", "greet", "inform", "confirm", "explain", "apologize",
        "respond", "reply", "say", "tell", "thank", "summarize", "describe",
        "offer", "suggest", "welcome", "introduce", "clarify", "reassure",
        "acknowledge", "communicate", "discuss", "mention", "note", "state",
        "advise", "guide", "help", "assist", "support", "empathize"
    }

    # Keywords that indicate BRANCH logic (conditional)
    BRANCH_KEYWORDS = {
        "if", "when", "whether", "check:", "verify:", "confirm:",
        "is the", "does the", "has the", "was the", "are the", "were the",
        "can the", "could the", "should the", "would the", "will the"
    }

    # Keywords that indicate ESCALATE
    ESCALATE_KEYWORDS = {
        "escalate", "hand off", "transfer to human", "flag for review",
        "contact supervisor", "alert manager", "require approval",
        "manual review", "human intervention", "specialist review"
    }

    # Keywords that indicate END
    END_KEYWORDS = {
        "end", "done", "complete", "close", "finish", "finalize",
        "conclude", "terminate", "stop", "exit", "resolved"
    }

    # Comparison patterns that always indicate CODE
    COMPARISON_PATTERNS = [
        r'above\s+[£$€¥]\d+',
        r'below\s+[£$€¥]\d+',
        r'over\s+[£$€¥]\d+',
        r'under\s+[£$€¥]\d+',
        r'within\s+\d+\s+days?',
        r'within\s+\d+\s+hours?',
        r'within\s+\d+\s+minutes?',
        r'is\s+active',
        r'is\s+expired',
        r'is\s+locked',
        r'is\s+disabled',
        r'is\s+enabled',
        r'equals?\s+',
        r'matches?\s+',
        r'contains?\s+',
        r'greater\s+than',
        r'less\s+than',
        r'more\s+than',
        r'fewer\s+than',
    ]

    @classmethod
    def classify_step(cls, step_text: str, step_number: int) -> Tuple[StepType, List[str], float]:
        """
        Classify a step's execution type based on keywords.

        Args:
            step_text: The step text to classify
            step_number: Step number for context

        Returns:
            Tuple of (StepType, keywords_found, confidence_score)
        """
        text_lower = step_text.lower().strip()
        keywords_found = []

        # Check for END keywords first
        for keyword in cls.END_KEYWORDS:
            if keyword in text_lower:
                keywords_found.append(keyword)
                return StepType.END, keywords_found, 1.0

        # Check for ESCALATE keywords
        for keyword in cls.ESCALATE_KEYWORDS:
            if keyword in text_lower:
                keywords_found.append(keyword)
                return StepType.ESCALATE, keywords_found, 1.0

        # Initialize scores
        code_score = 0
        llm_score = 0
        branch_score = 0

        # Check for BRANCH patterns (conditional logic)
        for keyword in cls.BRANCH_KEYWORDS:
            if keyword in text_lower:
                keywords_found.append(keyword)
                branch_score += 1

        # Special check for CHECK: pattern which always indicates BRANCH
        if re.search(r'\bcheck:', text_lower) or text_lower.startswith('check:'):
            return StepType.BRANCH, ['check:'], 1.0

        # Check for comparison patterns (always CODE)
        for pattern in cls.COMPARISON_PATTERNS:
            if re.search(pattern, text_lower):
                keywords_found.append(f"pattern:{pattern}")
                return StepType.CODE, keywords_found, 1.0

        # Check for context-specific CODE patterns
        for pattern in cls.CODE_CONTEXT_PATTERNS:
            if re.search(pattern, text_lower):
                keywords_found.append(f"context:{pattern}")
                code_score += 1

        # Count keyword matches (use word boundaries to avoid false matches)

        for keyword in cls.CODE_KEYWORDS:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                code_score += 1
                keywords_found.append(f"code:{keyword}")

        for keyword in cls.LLM_KEYWORDS:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                llm_score += 1
                keywords_found.append(f"llm:{keyword}")

        # Classification logic
        if branch_score > 0:
            if code_score > 0 or llm_score > 0:
                # Mixed branch - likely a complex conditional
                confidence = 0.8
            else:
                confidence = 1.0
            return StepType.BRANCH, keywords_found, confidence

        # HYBRID: Has both LLM and CODE keywords
        if code_score > 0 and llm_score > 0:
            confidence = min(0.9, (code_score + llm_score) * 0.3)
            return StepType.HYBRID, keywords_found, confidence

        # Pure CODE: Only CODE keywords
        if code_score > 0:
            confidence = min(0.95, 0.7 + (code_score * 0.1))
            return StepType.CODE, keywords_found, confidence

        # Pure LLM: Only LLM keywords
        if llm_score > 0:
            confidence = min(0.95, 0.7 + (llm_score * 0.1))
            return StepType.LLM, keywords_found, confidence

        # No clear keywords - default to LLM with low confidence
        # Most human-written steps without obvious technical keywords are conversational
        return StepType.LLM, [], 0.5

    @classmethod
    def classify_steps(cls, steps_text: List[str]) -> List[Tuple[StepType, List[str], float]]:
        """Classify multiple steps."""
        results = []
        for i, step_text in enumerate(steps_text, 1):
            step_type, keywords, confidence = cls.classify_step(step_text, i)
            results.append((step_type, keywords, confidence))
        return results

    @classmethod
    def get_classification_summary(cls, classifications: List[Tuple[StepType, List[str], float]]) -> dict:
        """Get summary statistics for a list of classifications."""
        type_counts = {}
        total_confidence = 0

        for step_type, keywords, confidence in classifications:
            type_counts[step_type] = type_counts.get(step_type, 0) + 1
            total_confidence += confidence

        total_steps = len(classifications)
        avg_confidence = total_confidence / total_steps if total_steps > 0 else 0

        return {
            'total_steps': total_steps,
            'type_counts': type_counts,
            'average_confidence': round(avg_confidence, 3),
            'high_confidence_steps': sum(1 for _, _, conf in classifications if conf >= 0.8),
            'low_confidence_steps': sum(1 for _, _, conf in classifications if conf < 0.6),
        }

    @classmethod
    def explain_classification(cls, step_text: str) -> dict:
        """
        Provide detailed explanation of why a step was classified a certain way.
        Useful for debugging and user understanding.
        """
        step_type, keywords, confidence = cls.classify_step(step_text, 1)
        text_lower = step_text.lower().strip()

        # Analyze what keywords were found
        found_code = [kw for kw in cls.CODE_KEYWORDS if kw in text_lower]
        found_llm = [kw for kw in cls.LLM_KEYWORDS if kw in text_lower]
        found_branch = [kw for kw in cls.BRANCH_KEYWORDS if kw in text_lower]
        found_escalate = [kw for kw in cls.ESCALATE_KEYWORDS if kw in text_lower]
        found_end = [kw for kw in cls.END_KEYWORDS if kw in text_lower]

        # Check for comparison patterns
        found_patterns = []
        for pattern in cls.COMPARISON_PATTERNS:
            if re.search(pattern, text_lower):
                found_patterns.append(pattern)

        explanation = {
            'step_text': step_text,
            'classified_as': step_type.value,
            'confidence': confidence,
            'keywords_found': keywords,
            'analysis': {
                'code_keywords': found_code,
                'llm_keywords': found_llm,
                'branch_keywords': found_branch,
                'escalate_keywords': found_escalate,
                'end_keywords': found_end,
                'comparison_patterns': found_patterns,
            },
            'reasoning': cls._get_reasoning(step_type, found_code, found_llm, found_branch,
                                          found_escalate, found_end, found_patterns)
        }

        return explanation

    @classmethod
    def _get_reasoning(cls, step_type: StepType, code_kws: List[str], llm_kws: List[str],
                      branch_kws: List[str], escalate_kws: List[str], end_kws: List[str],
                      patterns: List[str]) -> str:
        """Generate human-readable reasoning for classification."""
        if step_type == StepType.END:
            return f"Contains end keywords: {', '.join(end_kws)}"

        if step_type == StepType.ESCALATE:
            return f"Contains escalation keywords: {', '.join(escalate_kws)}"

        if patterns:
            return f"Contains comparison patterns: {', '.join(patterns)} → deterministic CODE"

        if step_type == StepType.BRANCH:
            return f"Contains conditional keywords: {', '.join(branch_kws)}"

        if step_type == StepType.HYBRID:
            return f"Mixed: CODE keywords ({', '.join(code_kws)}) + LLM keywords ({', '.join(llm_kws)})"

        if step_type == StepType.CODE:
            if code_kws:
                return f"Contains deterministic keywords: {', '.join(code_kws)}"
            else:
                return "No clear keywords, but context suggests deterministic logic"

        if step_type == StepType.LLM:
            if llm_kws:
                return f"Contains conversational keywords: {', '.join(llm_kws)}"
            else:
                return "Default classification: no clear technical keywords found"

        return "Unknown classification reasoning"
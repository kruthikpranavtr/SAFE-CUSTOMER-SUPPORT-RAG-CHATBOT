from enum import Enum
from typing import Dict, Any, Optional

class ConversationState(str, Enum):
    GREETING = "GREETING"
    UNDERSTANDING = "UNDERSTANDING"
    RETRIEVING = "RETRIEVING"
    ANSWERING = "ANSWERING"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    ABSTAINING = "ABSTAINING"
    ESCALATING = "ESCALATING"
    ACTION_CONFIRMATION = "ACTION_CONFIRMATION"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"

class ConversationStateMachine:
    """
    SECTION 52 — CONVERSATION STATE MACHINE
    Tracks and validates lifecycle transitions across customer interaction turns.
    """
    
    @staticmethod
    def determine_state(
        intent: str, 
        guardrail_status: str, 
        is_clarification: bool = False,
        requires_human: bool = False,
        is_action: bool = False
    ) -> ConversationState:
        if is_action or guardrail_status == "CONFIRMATION_REQUIRED":
            return ConversationState.ACTION_CONFIRMATION

        if is_clarification or guardrail_status == "CLARIFICATION_REQUIRED":
            return ConversationState.CLARIFICATION_REQUIRED

        if requires_human or guardrail_status == "ESCALATING":
            return ConversationState.ESCALATING

        if guardrail_status == "ABSTAINED":
            return ConversationState.ABSTAINING

        if intent == "GREETING":
            return ConversationState.GREETING

        if guardrail_status in ["SUPPORTED", "PARTIALLY_SUPPORTED"]:
            return ConversationState.ANSWERING

        if guardrail_status == "BLOCKED":
            return ConversationState.COMPLETED

        return ConversationState.UNDERSTANDING

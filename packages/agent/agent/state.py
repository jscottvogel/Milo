import operator
from collections.abc import Sequence
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    thread_id: str
    tenant_id: str
    # Messages in the current conversational window
    messages: Annotated[Sequence[BaseMessage], operator.add]

    # Context loaded from memory layers
    system_prompt: str

    # State tracking
    pending_tool_calls: list[dict[str, Any]]
    approvals_pending: list[dict[str, Any]]
    finish_reason: Literal["stop", "tool_calls", "approval_required", "max_turns", "max_cost", "human_handoff"] | None

    # Observability and guardrails
    turn_count: int
    iterations: int
    cost_usd: float

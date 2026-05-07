# ADR 0004: LangGraph vs Custom While Loop

## Status
Accepted

## Context
Milo requires a cyclic state machine capable of parsing inputs, routing to tools, interrupting for human-in-the-loop approvals, and continuing execution. The two primary options were building a custom `while` loop over Bedrock API responses or using a structured framework like LangGraph.

## Decision
We chose LangGraph (v0.2.x) to implement the agent runtime core.

## Consequences

**Positive:**
- **Built-in persistence**: LangGraph supports checkpointing and graph state saving out of the box, which naturally aligns with our "interrupt for approval" mechanics.
- **Type safety**: Graph state is explicitly typed via `AgentState` TypedDict.
- **Observability**: First-class integration with LangSmith or custom tracing for observing graph transitions.

**Negative:**
- **Complexity**: LangGraph introduces an abstraction layer over basic API calls, requiring developers to understand graph compilation and node transitions.
- **Overhead**: Minor performance overhead relative to raw loops, though negligible compared to LLM latency.

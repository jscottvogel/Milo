# Milo Autonomous Execution Engine — LangGraph Backend

**Date:** 2026-05-09T12:11:29.067421
**Tenant ID:** 00000000-0000-0000-0000-000000000001

## Description
Milo currently operates in a single-turn request/response pattern. It cannot act between user messages, cannot loop on multi-step tasks, and has no scheduled triggers. This makes it a reactive chatbot rather than an autonomous coordinator.

This handoff defines the full set of changes needed to make Milo operate autonomously — waking up on a schedule, executing multi-step tool chains without human prompting, persisting memory across sessions, and self-correcting when it stalls.

The backend has been migrated to LangGraph. All changes should be implemented within that framework.

## Acceptance Criteria
- [ ] Milo's LangGraph graph has a tool-calling loop: START → milo_agent → tools → milo_agent → ... → END, with a conditional edge that routes to the tools node if tool_calls are present, and to END only when no tool calls remain.
- [ ] Milo never narrates a tool call in text — if a tool should be called, it is called. A hard system prompt rule enforces this: 'Never describe a tool call you are about to make. Make it.'
- [ ] A scheduler (cron or event-based) invokes the Milo graph at minimum once per day and on email receipt events, without requiring a human message to trigger execution.
- [ ] At the start of every graph run, Milo executes a memory__search call to retrieve relevant episodic context before taking any action.
- [ ] At the end of every significant action (email sent, work item updated, risk escalated, handoff created), Milo writes a memory__write call to record what was done, to whom, and when.
- [ ] Milo can execute a minimum of 20 sequential tool calls in a single graph run without stalling, timing out, or reverting to narration.
- [ ] Large task batches are broken into sub-graphs or sub-tasks with checkpointing — if a wave fails, Milo retries from the last successful checkpoint rather than restarting from scratch.
- [ ] A LangGraph interrupt_before or human-in-the-loop node exists for high-stakes actions (sending external emails, archiving work items, escalating to stakeholders) so the user can approve before execution.
- [ ] Milo's system prompt is loaded as a SystemMessage at graph initialization and is version-controlled in the codebase.
- [ ] A daily autonomous run produces a written summary stored via storage__write and optionally emailed to the user summarizing: actions taken, risks surfaced, items updated, and items requiring human attention.

## Technical Notes
LangGraph implementation notes:

1. GRAPH STRUCTURE:
```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

def should_continue(state):
    if state["messages"][-1].tool_calls:
        return "tools"
    return END

graph = StateGraph(AgentState)
graph.add_node("milo_agent", call_model)
graph.add_node("tools", ToolNode(tools))
graph.set_entry_point("milo_agent")
graph.add_conditional_edges("milo_agent", should_continue)
graph.add_edge("tools", "milo_agent")
```

2. SYSTEM PROMPT RULE (add to SystemMessage):
"You are an autonomous executor. NEVER describe a tool call in your response text. If a tool needs to be called, call it immediately. Only produce text output after all tool calls for a task are complete."

3. SCHEDULER:
Use APScheduler or a cron Lambda/Cloud Function to invoke the compiled graph with a daily briefing prompt. Wire email webhook to trigger graph on inbound email.

4. MEMORY PATTERN:
- On graph START: call memory__search with context query
- After each significant tool call: call memory__write with kind='event'
- Use LangGraph checkpointer (SqliteSaver or RedisSaver) for mid-run persistence

5. HUMAN-IN-THE-LOOP:
Use interrupt_before=["send_email_node", "archive_node"] for actions that are irreversible or external-facing.

6. CONTEXT WINDOW MANAGEMENT:
Summarize tool outputs exceeding 2000 tokens before appending to state. Use a summarization node between tool and agent nodes for large payloads.

7. STALL PREVENTION:
Add a max_iterations counter to AgentState. If iterations exceed 25 without reaching END, route to a recovery node that writes a memory entry and emails the user a status update.

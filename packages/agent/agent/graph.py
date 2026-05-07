from langgraph.graph import END, StateGraph

from agent.state import AgentState


def perceive_node(state: AgentState):
    # Process incoming context, check budgets
    return {"turn_count": state.get("turn_count", 0) + 1}

def plan_node(state: AgentState):
    # For Phase 3, we just pass through
    return state

def act_node(state: AgentState):
    # LLM invocation happens in runner to stream events.
    # In a fully embedded graph, we'd invoke the LLM here.
    # For the PoC, we let the runner yield the stream, so this node
    # just marks transition to Observe or Reflect.
    return state

def observe_node(state: AgentState):
    # Execute tools
    return state

def reflect_node(state: AgentState):
    # Summarize working memory if too large
    return state

def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("Perceive", perceive_node)
    workflow.add_node("Plan", plan_node)
    workflow.add_node("Act", act_node)
    workflow.add_node("Observe", observe_node)
    workflow.add_node("Reflect", reflect_node)

    workflow.set_entry_point("Perceive")
    workflow.add_edge("Perceive", "Plan")
    workflow.add_edge("Plan", "Act")

    # Conditional logic for Act -> Observe (tools) vs Reflect (done)
    def should_observe(state: AgentState) -> str:
        if state.get("finish_reason") == "tool_calls":
            return "Observe"
        return "Reflect"

    workflow.add_conditional_edges("Act", should_observe, {
        "Observe": "Observe",
        "Reflect": "Reflect"
    })

    workflow.add_edge("Observe", "Act")
    workflow.add_edge("Reflect", END)

    return workflow.compile()

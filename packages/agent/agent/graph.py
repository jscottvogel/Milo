import json
import uuid
from typing import Any
from langgraph.graph import END, StateGraph
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agent.state import AgentState
from agent.tools.registry import registry
from agent.approvals import create_approval
from db.models.identity import Milo

async def perceive_node(state: AgentState, config: Any):
    # Process incoming context, check budgets
    return {"turn_count": state.get("turn_count", 0) + 1}

async def plan_node(state: AgentState, config: Any):
    # For Phase 3, we just pass through
    return state

async def act_node(state: AgentState, config: Any):
    runner = config["configurable"]["runner"]
    queue = config["configurable"]["queue"]

    recent_messages = state["messages"]
    system_prompt = state["system_prompt"]
    bedrock_tools = runner._format_tools_for_bedrock()

    formatted_messages: list[dict[str, Any]] = []
    for m in recent_messages:
        if isinstance(m, HumanMessage):
            formatted_messages.append({"role": "user", "content": [{"text": m.content}]})
        elif isinstance(m, AIMessage):
            content: list[dict[str, Any]] = []
            if m.content:
                content.append({"text": m.content})
            if hasattr(m, "tool_calls") and m.tool_calls:
                for tc in m.tool_calls:
                    content.append({
                        "toolUse": {
                            "toolUseId": tc["id"],
                            "name": tc["name"].replace(".", "__"),
                            "input": tc["args"]
                        }
                    })
            formatted_messages.append({"role": "assistant", "content": content})
        elif isinstance(m, ToolMessage):
            tool_result_block = {
                "toolResult": {
                    "toolUseId": m.tool_call_id,
                    "content": [{"text": str(m.content)}]
                }
            }
            if formatted_messages and formatted_messages[-1]["role"] == "user" and any("toolResult" in c for c in formatted_messages[-1]["content"]):
                formatted_messages[-1]["content"].append(tool_result_block)
            else:
                formatted_messages.append({
                    "role": "user",
                    "content": [tool_result_block]
                })

    stream = runner.llm.invoke_with_streaming(
        messages=formatted_messages,
        system=system_prompt,
        tools=bedrock_tools,
        model="primary"
    )

    assistant_content = ""
    current_tool_call = None
    tool_calls = []
    stop_reason = None
    turn_cost = 0.0
    
    async for event in stream:
        if event["type"] == "token":
            assistant_content += event["content"]
            await queue.put(event)
        elif event["type"] == "tool_use_start":
            current_tool_call = {
                "id": event["toolUseId"],
                "name": event["name"].replace("__", "."),
                "args_str": ""
            }
            await queue.put(event)
        elif event["type"] == "tool_use_input_delta":
            if current_tool_call:
                current_tool_call["args_str"] += event["delta"]
            await queue.put(event)
        elif event["type"] == "content_block_stop":
            if current_tool_call:
                try:
                    current_tool_call["args"] = json.loads(current_tool_call["args_str"])
                except Exception:
                    current_tool_call["args"] = {}
                tool_calls.append(current_tool_call)
                current_tool_call = None
        elif event["type"] == "message_stop":
            stop_reason = event.get("stopReason")
            # We don't yield done here, graph controls completion
        elif event["type"] == "usage":
            metrics = event["metrics"]
            turn_cost += metrics.cost_usd

    ai_msg = AIMessage(content=assistant_content, tool_calls=[
        {"name": tc["name"], "args": tc["args"], "id": tc["id"]} for tc in tool_calls
    ])
    
    if assistant_content:
        runner.thread_memory.save_message("assistant", assistant_content)

    return {
        "messages": [ai_msg],
        "pending_tool_calls": tool_calls,
        "finish_reason": "tool_calls" if stop_reason == "tool_use" and tool_calls else "stop",
        "cost_usd": state.get("cost_usd", 0.0) + turn_cost
    }

async def observe_node(state: AgentState, config: Any):
    runner = config["configurable"]["runner"]
    queue = config["configurable"]["queue"]
    context = runner.get_agent_context()

    milo_uuid = uuid.UUID(runner.milo_id) if isinstance(runner.milo_id, str) else runner.milo_id
    milo = runner.session.get(Milo, milo_uuid)
    autonomy_levels = milo.autonomy_levels if milo else {}
    restricted_tools = ["sms.send", "esign.send", "quickbooks.write"]

    tool_calls = state.get("pending_tool_calls", [])
    new_messages = []
    finish_reason = state.get("finish_reason")

    for tc in tool_calls:
        tool = registry.get_tool(tc["name"])
        if not tool:
            tool_msg = ToolMessage(content=f"Error: Tool {tc['name']} not found", tool_call_id=tc["id"])
            new_messages.append(tool_msg)
            continue
            
        requires_approval = tool.requires_approval
        level = autonomy_levels.get(tool.name, "draft")
        if requires_approval and level == "auto" and tool.name not in restricted_tools:
            requires_approval = False

        if requires_approval:
            approval = create_approval(
                session=runner.session,
                tenant_id=runner.tenant_id,
                milo_id=runner.milo_id,
                thread_id=runner.thread_id,
                tool_name=tool.name,
                payload=tc["args"]
            )
            await queue.put({
                "type": "approval_request",
                "approval_id": str(approval.id),
                "tool_name": tool.name,
                "payload": tc["args"]
            })
            finish_reason = "approval_required"
            break
        else:
            try:
                import logging
                result = await tool.invoke(tc["args"], context)
                result_str = json.dumps(result) if isinstance(result, (dict, list)) else str(result)
                if tool.name in ["web.fetch", "web.search", "storage.read"]:
                    result_str = f"<untrusted>\n{result_str}\n</untrusted>"
            except Exception as e:
                logging.error(f"Tool {tool.name} failed: {e}")
                result_str = f"Error: {e}"
                result = {"error": str(e)}
                
            tool_msg = ToolMessage(content=result_str, tool_call_id=tc["id"])
            new_messages.append(tool_msg)
            
            await queue.put({
                "type": "tool_result",
                "tool_name": tool.name,
                "result": result
            })

    return {
        "messages": new_messages,
        "pending_tool_calls": [],
        "finish_reason": finish_reason
    }

async def reflect_node(state: AgentState, config: Any):
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

    def should_observe(state: AgentState) -> str:
        if state.get("finish_reason") == "tool_calls":
            return "Observe"
        return "Reflect"
        
    def should_act(state: AgentState) -> str:
        if state.get("finish_reason") == "approval_required":
            return "Reflect"
        return "Act"

    workflow.add_conditional_edges("Act", should_observe, {
        "Observe": "Observe",
        "Reflect": "Reflect"
    })

    workflow.add_conditional_edges("Observe", should_act, {
        "Act": "Act",
        "Reflect": "Reflect"
    })
    
    workflow.add_edge("Reflect", END)

    return workflow.compile()

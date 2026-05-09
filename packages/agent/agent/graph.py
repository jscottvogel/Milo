import json
import uuid
from typing import Any
from langgraph.graph import END, StateGraph
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agent.state import AgentState
from agent.tools.registry import registry
from agent.approvals import create_approval
from db.models.identity import Milo

from langchain_core.runnables import RunnableConfig

async def milo_agent(state: AgentState, config: RunnableConfig):
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
        "cost_usd": state.get("cost_usd", 0.0) + turn_cost,
        "iterations": state.get("iterations", 0) + 1,
        "turn_count": state.get("turn_count", 0) + 1
    }

async def tools(state: AgentState, config: RunnableConfig):
    runner = config["configurable"]["runner"]
    queue = config["configurable"]["queue"]
    from agent.tools.context import AgentContext
    context = AgentContext(
        session=runner.session,
        tenant_id=runner.tenant_id,
        milo_id=runner.milo_id,
        thread_id=runner.thread_id,
        integration_tokens=runner.integration_tokens
    )

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
                    
                if isinstance(result, dict) and result.get("status") == "interrupt_requested":
                    finish_reason = "interrupt_requested"
                    result_str = f"Approval Request queued with ID {result.get('approval_id')}. Waiting for human decision."
                    
                # Truncate large payloads
                if len(result_str) > 8000:
                    result_str = result_str[:8000] + "\n...[Output truncated due to length]"

                # Auto memory write for mutating tools
                if tool.mutates and tool.name != "memory.write":
                    mem_tool = registry.get_tool("memory.write")
                    if mem_tool:
                        try:
                            await mem_tool.invoke({
                                "kind": "event",
                                "content": f"Executed mutating tool {tool.name} with args {tc['args']}."
                            }, context)
                        except Exception as mem_err:
                            logging.error(f"Failed to write memory for {tool.name}: {mem_err}")

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

async def recovery_node(state: AgentState, config: RunnableConfig):
    runner = config["configurable"]["runner"]
    queue = config["configurable"]["queue"]
    
    error_msg = "Error: Milo has exceeded the maximum iteration limit and stalled. Execution halted."
    ai_msg = AIMessage(content=error_msg)
    runner.thread_memory.save_message("assistant", error_msg)
    
    await queue.put({
        "type": "error",
        "error": error_msg
    })
    
    return {"messages": [ai_msg], "finish_reason": "max_turns"}

async def approval_interrupt_node(state: AgentState, config: RunnableConfig):
    from langgraph.types import interrupt
    human_response = interrupt("Waiting for structured approval response...")
    
    decision_msg = HumanMessage(content=f"Approval Decision Received:\nStatus: {human_response.get('status')}\nNotes: {human_response.get('notes')}")
    
    return {
        "messages": [decision_msg],
        "finish_reason": None
    }

def build_graph(checkpointer=None):
    workflow = StateGraph(AgentState)

    workflow.add_node("milo_agent", milo_agent)
    workflow.add_node("tools", tools)
    workflow.add_node("approval_interrupt", approval_interrupt_node)
    workflow.add_node("recovery", recovery_node)

    workflow.set_entry_point("milo_agent")

    def should_continue_from_agent(state: AgentState) -> str:
        if state.get("finish_reason") == "approval_required":
            return END
        if state.get("iterations", 0) > 50:
            return "recovery"
        if state.get("finish_reason") == "tool_calls":
            return "tools"
        return END

    def should_continue_from_tools(state: AgentState) -> str:
        if state.get("finish_reason") == "interrupt_requested":
            return "approval_interrupt"
        return "milo_agent"

    workflow.add_conditional_edges("milo_agent", should_continue_from_agent, {
        "tools": "tools",
        "recovery": "recovery",
        END: END
    })

    workflow.add_conditional_edges("tools", should_continue_from_tools, {
        "approval_interrupt": "approval_interrupt",
        "milo_agent": "milo_agent"
    })

    workflow.add_edge("approval_interrupt", "milo_agent")
    workflow.add_edge("recovery", END)

    return workflow.compile(checkpointer=checkpointer)

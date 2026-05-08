import datetime
import json
import logging
import os
import uuid
from collections.abc import AsyncGenerator
from typing import Any
import boto3
from langfuse import Langfuse

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from sqlalchemy.orm import Session

from agent.approvals import create_approval
from agent.llm.bedrock import BedrockClient, LLMUsage
from agent.memory.program import ProgramMemory
from agent.memory.thread import ThreadMemory
from agent.memory.working import WorkingMemory
from agent.prompts.builder import build_system_prompt
from agent.tools.context import AgentContext
from agent.tools.context import AgentContext
from agent.tools.registry import registry
from db.models import AgentRun
from db.models.identity import Milo

logger = logging.getLogger(__name__)

class AgentRunner:
    def __init__(self, session: Session, tenant_id: str, thread_id: str, milo_id: str):
        self.session = session
        self.tenant_id = tenant_id
        self.thread_id = thread_id
        self.milo_id = milo_id
        self.llm = BedrockClient()
        self.thread_memory = ThreadMemory(session, thread_id, tenant_id)
        self.program_memory = ProgramMemory(session)
        self.working_memory = WorkingMemory()
        self.integration_tokens = self._load_integration_tokens()
        self.langfuse = Langfuse() if os.getenv("LANGFUSE_PUBLIC_KEY") else None

    def _load_integration_tokens(self) -> dict[str, str]:
        tokens = {}
        
        # Load from environment variables (which should be set via .env)
        if os.getenv("NYLAS_GRANT_ID"):
            tokens["nylas_grant_id"] = os.getenv("NYLAS_GRANT_ID")
        if os.getenv("NYLAS_ORG_ID"):
            tokens["nylas_org_id"] = os.getenv("NYLAS_ORG_ID")
        try:
            ssm = boto3.client('ssm', region_name='us-east-1')
            param_name = f"/milo/tenants/{self.tenant_id}/integrations/gmail/token"
            response = ssm.get_parameter(Name=param_name, WithDecryption=True)
            tokens['gmail'] = response['Parameter']['Value']
        except Exception as e:
            logger.debug(f"Failed to load integration tokens from SSM: {e}")
        return tokens
        
    def _format_tools_for_bedrock(self) -> list[dict[str, Any]]:
        tools = []
        for t in registry.get_all_tools():
            schema = t.input_schema.model_json_schema()
            # Remove pydantic specific fields that might confuse bedrock
            if "$defs" in schema:
                del schema["$defs"]
            tools.append({
                "toolSpec": {
                    "name": t.name.replace(".", "__"),
                    "description": t.description,
                    "inputSchema": {
                        "json": schema
                    }
                }
            })
        return tools

    async def run_turn(self, user_message: str | None = None) -> AsyncGenerator[dict[str, Any], None]:
        # 1. Load context
        recent_messages = self.thread_memory.load_recent_messages()
        
        if user_message:
            recent_messages.append(HumanMessage(content=user_message))
            self.thread_memory.save_message("user", user_message)

        program_context = self.program_memory.get_context(milo_id=self.milo_id)

        # 2. Build system prompt
        system_prompt = build_system_prompt(
            persona_pack="sme",
            program_context=program_context
        )
        
        bedrock_tools = self._format_tools_for_bedrock()
        context = AgentContext(
            session=self.session,
            tenant_id=self.tenant_id,
            milo_id=self.milo_id,
            thread_id=self.thread_id,
            integration_tokens=self.integration_tokens
        )

        turn_cost = 0.0
        turn_input_tokens = 0
        turn_output_tokens = 0
        max_loops = 5
        loop_count = 0

        while loop_count < max_loops:
            loop_count += 1
            
            # Format messages for bedrock
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
                    # We must pack ToolMessages into a user message with toolResult
                    # If the last message was a 'user' message containing toolResults, append to it
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

            stream = self.llm.invoke_with_streaming(
                messages=formatted_messages,
                system=system_prompt,
                tools=bedrock_tools,
                model="primary"
            )

            assistant_content = ""
            current_tool_call = None
            tool_calls = []
            stop_reason = None

            async for event in stream:
                if event["type"] == "token":
                    assistant_content += event["content"]
                    yield event
                elif event["type"] == "tool_use_start":
                    current_tool_call = {
                        "id": event["toolUseId"],
                        "name": event["name"].replace("__", "."),
                        "args_str": ""
                    }
                    yield event
                elif event["type"] == "tool_use_input_delta":
                    if current_tool_call:
                        current_tool_call["args_str"] += event["delta"]
                    yield event
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
                    yield {"type": "done", "reason": stop_reason}
                elif event["type"] == "usage":
                    metrics: LLMUsage = event["metrics"]
                    turn_cost += metrics.cost_usd
                    turn_input_tokens += metrics.input_tokens
                    turn_output_tokens += metrics.output_tokens

            # Save assistant message with potential tool calls
            ai_msg = AIMessage(content=assistant_content, tool_calls=[
                {"name": tc["name"], "args": tc["args"], "id": tc["id"]} for tc in tool_calls
            ])
            recent_messages.append(ai_msg)
            
            # Save the raw text content to thread memory if there was any
            if assistant_content:
                self.thread_memory.save_message("assistant", assistant_content)
                # Tool calls are typically saved to ToolCall db model, but we skip deep persistence for PoC unless needed
                
            if stop_reason == "tool_use" and tool_calls:
                # Fetch Milo autonomy levels
                milo_uuid = uuid.UUID(self.milo_id) if isinstance(self.milo_id, str) else self.milo_id
                milo = self.session.get(Milo, milo_uuid)
                autonomy_levels = milo.autonomy_levels if milo else {}
                restricted_tools = ["sms.send", "esign.send", "quickbooks.write"]

                # Process tool calls
                needs_approval = False
                for tc in tool_calls:
                    tool = registry.get_tool(tc["name"])
                    if not tool:
                        # Yield error
                        tool_msg = ToolMessage(content=f"Error: Tool {tc['name']} not found", tool_call_id=tc["id"])
                        recent_messages.append(tool_msg)
                        continue
                        
                    requires_approval = tool.requires_approval
                    level = autonomy_levels.get(tool.name, "draft")
                    if requires_approval and level == "auto" and tool.name not in restricted_tools:
                        requires_approval = False

                    if requires_approval:
                        # Create approval and pause
                        approval = create_approval(
                            session=self.session,
                            tenant_id=self.tenant_id,
                            milo_id=self.milo_id,
                            thread_id=self.thread_id,
                            tool_name=tool.name,
                            payload=tc["args"]
                        )
                        yield {
                            "type": "approval_request",
                            "approval_id": str(approval.id),
                            "tool_name": tool.name,
                            "payload": tc["args"]
                        }
                        needs_approval = True
                        break # Stop processing other tools if one needs approval
                    else:
                        # Execute automatically
                        try:
                            result = await tool.invoke(tc["args"], context)
                            result_str = json.dumps(result) if isinstance(result, (dict, list)) else str(result)
                            # Wrap untrusted content (Phase 4 requirement)
                            if tool.name in ["web.fetch", "web.search", "storage.read"]:
                                result_str = f"<untrusted>\n{result_str}\n</untrusted>"
                        except Exception as e:
                            logger.error(f"Tool {tool.name} failed: {e}")
                            result_str = f"Error: {e}"
                            result = {"error": str(e)}
                            
                        tool_msg = ToolMessage(content=result_str, tool_call_id=tc["id"])
                        recent_messages.append(tool_msg)
                        
                        yield {
                            "type": "tool_result",
                            "tool_name": tool.name,
                            "result": result
                        }
                        
                if needs_approval:
                    break # Break out of loop, run is paused
            else:
                break # Not a tool use, or no tool calls, run is complete

        # Persist AgentRun
        run = AgentRun(
            tenant_id=uuid.UUID(self.tenant_id) if isinstance(self.tenant_id, str) else self.tenant_id,
            milo_id=uuid.UUID(self.milo_id) if isinstance(self.milo_id, str) else self.milo_id,
            thread_id=uuid.UUID(self.thread_id) if isinstance(self.thread_id, str) else self.thread_id,
            started_at=datetime.datetime.now(datetime.UTC),
            status="done" if not tool_calls or not tool_calls[-1].get("requires_approval") else "paused",
            total_input_tokens=turn_input_tokens,
            total_output_tokens=turn_output_tokens,
            cost_usd=turn_cost,
            turn_count=loop_count
        )
        self.session.add(run)
        self.session.commit()

        # Emit CloudWatch Custom Metrics
        try:
            cw = boto3.client('cloudwatch', region_name='us-east-1')
            cw.put_metric_data(
                Namespace='Milo',
                MetricData=[
                    {'MetricName': 'tokens_in', 'Value': turn_input_tokens, 'Unit': 'Count'},
                    {'MetricName': 'tokens_out', 'Value': turn_output_tokens, 'Unit': 'Count'},
                    {'MetricName': 'cost_usd', 'Value': turn_cost, 'Unit': 'Count'},
                    {'MetricName': 'tool_calls', 'Value': len(tool_calls), 'Unit': 'Count'}
                ]
            )
        except Exception as e:
            logger.debug(f"Failed to emit CW metrics: {e}")


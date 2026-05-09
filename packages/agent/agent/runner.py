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
        nylas_grant_id = os.getenv("NYLAS_GRANT_ID")
        if nylas_grant_id:
            tokens["nylas_grant_id"] = nylas_grant_id
            
        nylas_org_id = os.getenv("NYLAS_ORG_ID")
        if nylas_org_id:
            tokens["nylas_org_id"] = nylas_org_id
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

        import asyncio
        from agent.graph import build_graph
        from agent.state import AgentState

        turn_cost = 0.0
        turn_input_tokens = 0
        turn_output_tokens = 0
        
        stream_queue = asyncio.Queue()

        async def _run_graph():
            try:
                workflow = build_graph()
                config = {"configurable": {"runner": self, "queue": stream_queue}}
                
                state: AgentState = {
                    "thread_id": self.thread_id,
                    "tenant_id": self.tenant_id,
                    "messages": recent_messages,
                    "system_prompt": system_prompt,
                    "pending_tool_calls": [],
                    "approvals_pending": [],
                    "finish_reason": None,
                    "turn_count": 0,
                    "cost_usd": 0.0
                }
                
                final_state = await workflow.ainvoke(state, config=config)
                
                # Persist AgentRun after graph finishes
                turn_cost = final_state.get("cost_usd", 0.0)
                turn_count = final_state.get("turn_count", 0)
                
                run = AgentRun(
                    tenant_id=uuid.UUID(self.tenant_id) if isinstance(self.tenant_id, str) else self.tenant_id,
                    milo_id=uuid.UUID(self.milo_id) if isinstance(self.milo_id, str) else self.milo_id,
                    thread_id=uuid.UUID(self.thread_id) if isinstance(self.thread_id, str) else self.thread_id,
                    started_at=datetime.datetime.now(datetime.UTC),
                    status="paused" if final_state.get("finish_reason") == "approval_required" else "done",
                    total_input_tokens=0,
                    total_output_tokens=0,
                    cost_usd=turn_cost,
                    turn_count=turn_count
                )
                self.session.add(run)
                self.session.commit()

                # Emit CloudWatch Custom Metrics
                try:
                    cw = boto3.client('cloudwatch', region_name='us-east-1')
                    cw.put_metric_data(
                        Namespace='Milo',
                        MetricData=[
                            {'MetricName': 'cost_usd', 'Value': turn_cost, 'Unit': 'Count'}
                        ]
                    )
                except Exception as e:
                    logger.debug(f"Failed to emit CW metrics: {e}")
                
                await stream_queue.put({"type": "done", "reason": final_state.get("finish_reason")})
            except Exception as e:
                import traceback
                traceback.print_exc()
                await stream_queue.put({"type": "error", "error": str(e)})

        # Start the graph in the background
        task = asyncio.create_task(_run_graph())

        # Yield events from the queue until graph completion
        while True:
            event = await stream_queue.get()
            if event["type"] in ["done", "error"]:
                yield event
                break
            elif event["type"] == "approval_request":
                # Yield the approval, and then we will eventually yield done when the graph stops
                yield event
            else:
                yield event

    async def run_autonomous_turn(self, trigger_reason: str) -> None:
        """Run the agent graph asynchronously without yielding SSE events to a UI client."""
        import asyncio
        from agent.graph import build_graph
        from agent.state import AgentState

        # 1. Load context
        recent_messages = self.thread_memory.load_recent_messages()
        
        trigger_message = f"Autonomous Trigger: {trigger_reason}"
        recent_messages.append(HumanMessage(content=trigger_message))
        self.thread_memory.save_message("user", trigger_message)

        program_context = self.program_memory.get_context(milo_id=self.milo_id)

        # 2. Build system prompt
        system_prompt = build_system_prompt(
            persona_pack="sme",
            program_context=program_context
        )
        
        # 3. Setup dummy Queue to satisfy graph.py's expectation, and consume it silently
        stream_queue = asyncio.Queue()
        
        async def _consume_queue():
            while True:
                event = await stream_queue.get()
                if event["type"] in ["done", "error"]:
                    break
                    
        consumer_task = asyncio.create_task(_consume_queue())

        try:
            workflow = build_graph()
            config = {"configurable": {"runner": self, "queue": stream_queue}}
            
            state: AgentState = {
                "thread_id": self.thread_id,
                "tenant_id": self.tenant_id,
                "messages": recent_messages,
                "system_prompt": system_prompt,
                "pending_tool_calls": [],
                "approvals_pending": [],
                "finish_reason": None,
                "turn_count": 0,
                "cost_usd": 0.0
            }
            
            final_state = await workflow.ainvoke(state, config=config)
            
            # Persist AgentRun after graph finishes
            turn_cost = final_state.get("cost_usd", 0.0)
            turn_count = final_state.get("turn_count", 0)
            
            run = AgentRun(
                tenant_id=uuid.UUID(self.tenant_id) if isinstance(self.tenant_id, str) else self.tenant_id,
                milo_id=uuid.UUID(self.milo_id) if isinstance(self.milo_id, str) else self.milo_id,
                thread_id=uuid.UUID(self.thread_id) if isinstance(self.thread_id, str) else self.thread_id,
                started_at=datetime.datetime.now(datetime.UTC),
                status="paused" if final_state.get("finish_reason") == "approval_required" else "done",
                total_input_tokens=0,
                total_output_tokens=0,
                cost_usd=turn_cost,
                turn_count=turn_count
            )
            self.session.add(run)
            self.session.commit()

            # Emit CloudWatch Custom Metrics
            try:
                cw = boto3.client('cloudwatch', region_name='us-east-1')
                cw.put_metric_data(
                    Namespace='Milo',
                    MetricData=[
                        {'MetricName': 'cost_usd', 'Value': turn_cost, 'Unit': 'Count'}
                    ]
                )
            except Exception as e:
                logger.debug(f"Failed to emit CW metrics: {e}")
            
            await stream_queue.put({"type": "done", "reason": final_state.get("finish_reason")})
        except Exception as e:
            import traceback
            traceback.print_exc()
            await stream_queue.put({"type": "error", "error": str(e)})

        await consumer_task


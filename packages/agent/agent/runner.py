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
        
    def _clean_schema_for_bedrock(self, schema: dict[str, Any]):
        schema.pop("title", None)
        schema.pop("default", None)
        schema.pop("$defs", None)
        if "properties" in schema:
            for prop in schema["properties"].values():
                if isinstance(prop, dict):
                    self._clean_schema_for_bedrock(prop)
        if "items" in schema and isinstance(schema["items"], dict):
            self._clean_schema_for_bedrock(schema["items"])

    def _format_tools_for_bedrock(self) -> list[dict[str, Any]]:
        tools = []
        for t in registry.get_all_tools():
            schema = t.input_schema.model_json_schema()
            self._clean_schema_for_bedrock(schema)
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

        # 2. Pre-flight memory search
        memory_injections = ""
        mem_tool = registry.get_tool("memory.search")
        if mem_tool and user_message:
            context = AgentContext(
                session=self.session,
                tenant_id=self.tenant_id,
                milo_id=self.milo_id,
                thread_id=self.thread_id,
                integration_tokens=self.integration_tokens
            )
            try:
                search_res = await mem_tool.invoke({"query": user_message, "limit": 5}, context)
                if search_res and "results" in search_res:
                    memory_injections = "\n".join([str(r) for r in search_res["results"]])
            except Exception as e:
                logger.error(f"Pre-flight memory search failed: {e}")

        # 3. Build system prompt
        system_prompt = build_system_prompt(
            persona_pack="sme",
            program_context=program_context,
            memory_injections=memory_injections
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

        # 2. Pre-flight memory search
        memory_injections = ""
        mem_tool = registry.get_tool("memory.search")
        if mem_tool:
            context = AgentContext(
                session=self.session,
                tenant_id=self.tenant_id,
                milo_id=self.milo_id,
                thread_id=self.thread_id,
                integration_tokens=self.integration_tokens
            )
            try:
                search_res = await mem_tool.invoke({"query": trigger_reason, "limit": 5}, context)
                if search_res and "results" in search_res:
                    memory_injections = "\n".join([str(r) for r in search_res["results"]])
            except Exception as e:
                logger.error(f"Pre-flight memory search failed: {e}")

        # 3. Build system prompt
        system_prompt = build_system_prompt(
            persona_pack="sme",
            program_context=program_context,
            memory_injections=memory_injections
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
            from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
            from agent.graph import build_graph
            from agent.state import AgentState
            
            async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
                workflow = build_graph(checkpointer=checkpointer)
                config = {"configurable": {"thread_id": self.thread_id, "runner": self, "queue": stream_queue}, "recursion_limit": 50}
            
                state: AgentState = {
                    "thread_id": self.thread_id,
                    "tenant_id": self.tenant_id,
                    "messages": recent_messages,
                    "system_prompt": system_prompt,
                    "pending_tool_calls": [],
                    "approvals_pending": [],
                    "finish_reason": None,
                    "turn_count": 0,
                    "iterations": 0,
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
                
            # Write daily run log
            try:
                storage_tool = registry.get_tool("storage.write")
                if storage_tool:
                    context = AgentContext(
                        session=self.session,
                        tenant_id=self.tenant_id,
                        milo_id=self.milo_id,
                        thread_id=self.thread_id,
                        integration_tokens=self.integration_tokens
                    )
                    today = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
                    summary_content = f"Autonomous Run: {trigger_reason}\nThread: {self.thread_id}\nCost: ${turn_cost:.4f}\n"
                    await storage_tool.invoke({
                        "path": f"logs/daily_run_{today}.md",
                        "content": summary_content,
                        "append": True
                    }, context)
            except Exception as e:
                logger.error(f"Failed to write daily run log: {e}")
            
            await stream_queue.put({"type": "done", "reason": final_state.get("finish_reason")})
        except RecursionError as re:
            error_msg = "Milo stalled due to recursion limit (50 steps)."
            logger.error(error_msg)
            try:
                email_tool = registry.get_tool("email.send")
                context = AgentContext(
                    session=self.session,
                    tenant_id=self.tenant_id,
                    milo_id=self.milo_id,
                    thread_id=self.thread_id,
                    integration_tokens=self.integration_tokens
                )
                if email_tool:
                    await email_tool.invoke({
                        "to": ["j_scott_vogel@yahoo.com"],
                        "subject": "System Alert: Milo Execution Stalled",
                        "body": f"Milo autonomous execution stalled and self-terminated.\nReason: {trigger_reason}\nThread ID: {self.thread_id}"
                    }, context)
            except Exception as e:
                logger.error(f"Failed to send recovery email: {e}")
            await stream_queue.put({"type": "error", "error": error_msg})
        except Exception as e:
            import traceback
            traceback.print_exc()
            await stream_queue.put({"type": "error", "error": str(e)})

        await consumer_task

    async def resume_turn(self, approval_id: str, decision: str, notes: str | None = None) -> None:
        """Resume the LangGraph thread from an interrupt."""
        from langgraph.types import Command
        import traceback
        from agent.graph import build_graph
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        
        stream_queue = asyncio.Queue()
        
        response_payload = {
            "status": decision,
            "notes": notes,
            "approval_id": approval_id
        }
        
        async def _consume_queue():
            while True:
                event = await stream_queue.get()
                if event["type"] in ["done", "error"]:
                    break
                    
        consumer_task = asyncio.create_task(_consume_queue())
        
        try:
            async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
                workflow = build_graph(checkpointer=checkpointer)
                config = {
                    "configurable": {
                        "thread_id": self.thread_id,
                        "runner": self,
                        "queue": stream_queue
                    },
                    "recursion_limit": 50
                }
                final_state = await workflow.ainvoke(Command(resume=response_payload), config=config)
            await stream_queue.put({"type": "done", "reason": "resumed_and_finished"})
        except Exception as e:
            traceback.print_exc()
            await stream_queue.put({"type": "error", "error": str(e)})
            
        await consumer_task


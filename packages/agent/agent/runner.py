import datetime
import logging
from collections.abc import AsyncGenerator
from typing import Any

from db.models import AgentRun
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from agent.llm.bedrock import BedrockClient, LLMUsage
from agent.memory.program import ProgramMemory
from agent.memory.thread import ThreadMemory
from agent.memory.working import WorkingMemory
from agent.prompts.builder import build_system_prompt

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

    async def run_turn(self, user_message: str) -> AsyncGenerator[dict[str, Any], None]:
        # 1. Load context
        recent_messages = self.thread_memory.load_recent_messages()
        recent_messages.append(HumanMessage(content=user_message))
        self.thread_memory.save_message("user", user_message)

        program_context = self.program_memory.get_context() # Placeholder

        # 2. Build system prompt
        system_prompt = build_system_prompt(
            persona_pack="sme",
            program_context=program_context
        )

        # 3. Stream from LLM
        # For Phase 3, we format messages for bedrock (dict format)
        formatted_messages = []
        for m in recent_messages:
            role = "user" if isinstance(m, HumanMessage) else "assistant"
            formatted_messages.append({"role": role, "content": [{"text": m.content}]})

        stream = self.llm.invoke_with_streaming(
            messages=formatted_messages,
            system=system_prompt,
            tools=[], # No tools yet
            model="primary"
        )

        assistant_content = ""
        total_cost = 0.0

        async for event in stream:
            if event["type"] == "token":
                assistant_content += event["content"]
                yield event
            elif event["type"] == "usage":
                metrics: LLMUsage = event["metrics"]
                total_cost += metrics.cost_usd

                # Persist AgentRun
                run = AgentRun(
                    tenant_id=self.tenant_id,
                    milo_id=self.milo_id,
                    thread_id=self.thread_id,
                    started_at=datetime.datetime.now(datetime.UTC),
                    status="done",
                    total_input_tokens=metrics.input_tokens,
                    total_output_tokens=metrics.output_tokens,
                    cost_usd=metrics.cost_usd,
                    turn_count=1
                )
                self.session.add(run)
                self.session.commit()
            elif event["type"] == "message_stop":
                yield {"type": "done", "reason": event.get("stopReason")}

        # Save assistant message
        if assistant_content:
            self.thread_memory.save_message("assistant", assistant_content)

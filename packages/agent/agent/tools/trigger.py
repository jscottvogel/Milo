import os
import yaml
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field

from db.models.agent import Thread
from agent.tools.context import AgentContext
from agent.tools.registry import Tool
from agent.runner import AgentRunner


class TriggerEvaluateInput(BaseModel):
    rule_id: Optional[str] = Field(None, description="Optional rule ID to evaluate. If omitted, all rules are evaluated.")


class TriggerEvaluateOutput(BaseModel):
    results: list[dict[str, Any]] = Field(description="Results of the evaluated rules")


class TriggerEvaluateTool(Tool):
    name = "trigger.evaluate"
    description = "Evaluate all configured trigger rules and fire any actions whose conditions are met."
    input_schema = TriggerEvaluateInput
    output_schema = TriggerEvaluateOutput
    mutates = True
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        # Load rules from yaml
        rules_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "triggers", "rules.yaml")
        if not os.path.exists(rules_path):
            return TriggerEvaluateOutput(results=[{"error": f"Rules file not found at {rules_path}"}]).model_dump()

        with open(rules_path, "r") as f:
            data = yaml.safe_load(f)
            rules = data.get("rules", [])

        rule_id_filter = input_data.get("rule_id")
        if rule_id_filter:
            rules = [r for r in rules if r.get("id") == rule_id_filter]

        results = []
        for rule in rules:
            rule_id = rule.get("id")
            description = rule.get("description")
            action = rule.get("trigger_action")

            prompt = (
                f"[PROACTIVE TRIGGER CHECK: {rule_id}]\n"
                f"Your task is to evaluate the following condition: '{description}'.\n"
                f"You MUST use your tools (like email.read, calendar.read, work_item.read, etc.) to check if this condition is met.\n"
                f"If the condition is NOT met, simply state that the condition is not met and stop.\n"
                f"If the condition IS met, you MUST execute the following action using your tools: '{action}'.\n"
                f"CRITICAL: Before taking the action, search your memory to ensure you have not already taken this exact action today. If you have, do NOT take it again.\n"
                f"After taking the action, write a memory entry confirming that you fired the '{rule_id}' trigger today."
            )

            # Create a Thread explicitly to prevent ForeignKeyViolation
            new_thread_id = uuid.uuid4()
            new_thread = Thread(
                id=new_thread_id,
                tenant_id=uuid.UUID(context.tenant_id),
                milo_id=uuid.UUID(context.milo_id),
                summary=f"Proactive Trigger Evaluation: {rule_id}"
            )
            context.session.add(new_thread)
            context.session.commit()

            # We create a new runner instance with a new thread for this evaluation
            runner = AgentRunner(
                session=context.session,
                tenant_id=context.tenant_id,
                thread_id=str(new_thread_id),
                milo_id=context.milo_id
            )
            
            # Consume the generator to run the agent synchronously from the tool's perspective
            action_taken = False
            async for event in runner.run_turn(prompt):
                if event.get("type") == "tool_use_start" and event.get("name") == "email.send":
                    action_taken = True

            results.append({
                "rule_id": rule_id,
                "evaluated": True,
                "action_taken_in_evaluation": action_taken
            })

        return TriggerEvaluateOutput(results=results).model_dump()

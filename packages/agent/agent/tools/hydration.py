import json
import uuid
import os
import asyncio
from typing import Any

from pydantic import BaseModel, Field

from agent.tools.context import AgentContext
from agent.tools.registry import Tool
from agent.tools.file import FileReadTool
from agent.llm.bedrock import BedrockClient

class ExtractManifestInput(BaseModel):
    file_path: str = Field(description="Path to the document to extract from (e.g. uploads/...)")

class ExtractManifestOutput(BaseModel):
    run_id: str
    manifest_summary: str
    manifest_preview: str

class ExtractManifestTool(Tool):
    name = "program.extract_manifest"
    description = "Read a document, extract a structured hydration manifest JSON, and stage it for execution."
    input_schema = ExtractManifestInput
    output_schema = ExtractManifestOutput
    mutates = True
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        file_tool = FileReadTool()
        file_res = await file_tool.invoke({"file_path": input_data["file_path"]}, context)
        if "error" in file_res:
            return file_res
            
        content = file_res["content"]
        
        system_prompt = """You are an expert technical program manager.
Extract the program hierarchy from the document and return it STRICTLY as a valid JSON object matching this schema:
{
  "objective": { "name": "...", "description": "...", "status": "..." },
  "outcomes": [ { "name": "...", "description": "...", "status": "..." } ],
  "key_results": [ { "name": "...", "parent": "outcome_name", "description": "..." } ],
  "initiatives": [ { "name": "...", "parent": "outcome_name", "description": "..." } ],
  "projects": [ { "name": "...", "parent": "initiative_name", "description": "..." } ],
  "workstreams": [ { "name": "...", "parent": "project_name", "description": "..." } ],
  "milestones": [ { "name": "...", "parent": "workstream_name", "due_date": "...", "description": "..." } ],
  "tasks": [ { "name": "...", "parent": "milestone_name", "description": "..." } ],
  "risks": [ { "title": "...", "likelihood": 3, "impact": 3, "mitigation": "...", "parent": "project_name" } ],
  "decisions": [ { "title": "...", "decision_text": "...", "parent": "project_name" } ],
  "stakeholders": [ { "name": "...", "role": "...", "email": "...", "influence": "...", "interest": "..." } ]
}
Do not return anything other than the JSON object."""

        messages = [
            {"role": "user", "content": [{"text": f"Document content:\n\n{content[:150000]}\n\nExtract the JSON manifest."}]}
        ]
        
        bedrock = BedrockClient()
        response_text = ""
        try:
            async for event in bedrock.invoke_with_streaming(messages=messages, system=system_prompt, tools=[], model="primary"):
                if event["type"] == "token":
                    response_text += event["content"]
        except Exception as e:
            return {"error": f"LLM Extraction failed: {e}"}
            
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON object found")
            json_str = response_text[start_idx:end_idx]
            manifest = json.loads(json_str)
        except Exception as e:
            return {"error": f"Failed to parse LLM output as JSON: {e}", "raw_output": response_text[:1000]}
            
        manifest["_meta"] = {
            "source_document": os.path.basename(input_data["file_path"])
        }
            
        run_id = str(uuid.uuid4())
        
        import boto3
        s3 = boto3.client("s3")
        bucket = os.environ.get("S3_BUCKET_NAME", "milo-poc-bucket-jsco")
        key = f"{context.tenant_id}/hydration_runs/{run_id}/manifest.json"
        
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(manifest, indent=2)))
        
        summary = f"Extracted manifest ready. Run ID: {run_id}\n"
        for k, v in manifest.items():
            if k == "_meta": continue
            if isinstance(v, list):
                summary += f"- {len(v)} {k}\n"
            else:
                summary += f"- 1 {k}\n"
                
        return ExtractManifestOutput(
            run_id=run_id,
            manifest_summary=summary,
            manifest_preview=json.dumps(manifest, indent=2)[:1000] + "..."
        ).model_dump()


class ExecuteHydrationInput(BaseModel):
    run_id: str = Field(description="The UUID of the hydration run to execute.")

class ExecuteHydrationOutput(BaseModel):
    status: str
    message: str

class ExecuteHydrationTool(Tool):
    name = "program.execute_hydration"
    description = "Triggers the async Sequential Hydration Engine for a previously extracted manifest run_id."
    input_schema = ExecuteHydrationInput
    output_schema = ExecuteHydrationOutput
    mutates = True
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        run_id = input_data["run_id"]
        import httpx
        
        api_url = os.environ.get("API_URL", "http://localhost:8000")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{api_url}/v1/work_items/hydration/{run_id}/execute",
                    headers={"Authorization": f"Bearer dev_{context.tenant_id}"}
                )
                resp.raise_for_status()
                return ExecuteHydrationOutput(
                    status="started",
                    message=f"[HYDRATION_RUN:{run_id}]\nHydration engine triggered for run {run_id}. Watch the UI panel for progress."
                ).model_dump()
        except Exception as e:
            return {"error": f"Failed to trigger hydration engine: {e}"}


class ReconcileDiffInput(BaseModel):
    run_id: str = Field(description="The UUID of the hydration run containing the manifest.")

class ReconcileDiffOutput(BaseModel):
    summary: str
    to_create_count: int
    to_reparent_count: int
    to_archive_count: int
    already_correct_count: int

class ReconcileDiffTool(Tool):
    name = "program.reconcile_diff"
    description = "Reads a hydration manifest, compares it to the database, and produces a reconciliation diff (to_create, to_reparent, to_archive, already_correct)."
    input_schema = ReconcileDiffInput
    output_schema = ReconcileDiffOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        run_id = input_data["run_id"]
        
        import boto3
        s3 = boto3.client("s3")
        bucket = os.environ.get("S3_BUCKET_NAME", "milo-poc-bucket-jsco")
        manifest_key = f"{context.tenant_id}/hydration_runs/{run_id}/manifest.json"
        
        try:
            obj = s3.get_object(Bucket=bucket, Key=manifest_key)
            manifest = json.loads(obj['Body'].read())
        except Exception as e:
            return {"error": f"Failed to read manifest for run {run_id}: {e}"}
            
        from sqlalchemy import select
        from db.models.program import WorkItem, Risk, Decision, ChangeRequest, Stakeholder, Commitment
        
        db = context.session
        tenant_id = uuid.UUID(context.tenant_id)
        
        # Load all DB entities
        db_items = db.scalars(select(WorkItem).where(WorkItem.tenant_id == tenant_id, WorkItem.status != 'archived')).all()
        db_risks = db.scalars(select(Risk).where(Risk.tenant_id == tenant_id, Risk.status != 'archived')).all()
        db_decisions = db.scalars(select(Decision).where(Decision.tenant_id == tenant_id)).all()
        
        id_to_name = {str(item.id): item.name for item in db_items}
        
        db_entities = []
        for item in db_items:
            parent_name = id_to_name.get(str(item.parent_id)) if item.parent_id else None
            db_entities.append({"id": str(item.id), "name": item.name, "type": item.item_type, "parent_name": parent_name})
            
        for r in db_risks:
            parent_name = id_to_name.get(str(r.work_item_id)) if r.work_item_id else None
            db_entities.append({"id": str(r.id), "name": r.title, "type": "risk", "parent_name": parent_name})
            
        for d in db_decisions:
            parent_name = id_to_name.get(str(d.work_item_id)) if d.work_item_id else None
            db_entities.append({"id": str(d.id), "name": d.title, "type": "decision", "parent_name": parent_name})
            
        # Manifest entities
        manifest_entities = []
        for layer, items in manifest.items():
            if layer == "_meta": continue
            if isinstance(items, dict): items = [items]
            for item in items:
                name = item.get("name") or item.get("title") or item.get("description")
                if not name: continue
                entity_type = layer[:-1] if layer.endswith('s') and layer not in ["risks", "decisions", "stakeholders", "outcomes", "key_results", "projects", "workstreams", "milestones", "tasks"] else layer
                if layer == "objective": entity_type = "objective"
                elif layer == "outcomes": entity_type = "outcome"
                elif layer == "key_results": entity_type = "key_result"
                elif layer == "initiatives": entity_type = "initiative"
                elif layer == "projects": entity_type = "project"
                elif layer == "workstreams": entity_type = "workstream"
                elif layer == "milestones": entity_type = "milestone"
                elif layer == "tasks": entity_type = "task"
                elif layer == "risks": entity_type = "risk"
                elif layer == "decisions": entity_type = "decision"
                elif layer == "stakeholders": entity_type = "stakeholder"
                
                manifest_entities.append({
                    "name": name,
                    "type": entity_type,
                    "parent_name": item.get("parent"),
                    "raw": item
                })
                
        to_create = []
        to_reparent = []
        to_archive = []
        already_correct = []
        
        # Check DB against manifest
        for db_e in db_entities:
            matched_man = next((m for m in manifest_entities if m["name"] == db_e["name"] and m["type"] == db_e["type"]), None)
            if not matched_man:
                to_archive.append(db_e)
            else:
                if matched_man.get("parent_name") != db_e.get("parent_name"):
                    to_reparent.append({"id": db_e["id"], "name": db_e["name"], "type": db_e["type"], "old_parent": db_e.get("parent_name"), "new_parent": matched_man.get("parent_name")})
                else:
                    already_correct.append(db_e)
                    
        # Check Manifest against DB
        for man_e in manifest_entities:
            matched_db = next((d for d in db_entities if d["name"] == man_e["name"] and d["type"] == man_e["type"]), None)
            if not matched_db:
                to_create.append(man_e)
                
        diff = {
            "to_create": to_create,
            "to_reparent": to_reparent,
            "to_archive": to_archive,
            "already_correct": already_correct
        }
        diff_key = f"{context.tenant_id}/hydration_runs/{run_id}/diff.json"
        
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: s3.put_object(Bucket=bucket, Key=diff_key, Body=json.dumps(diff, indent=2)))
        
        summary = (
            f"Reconciliation Diff for Run {run_id}:\n"
            f"- To Create: {len(to_create)} entities\n"
            f"- To Reparent: {len(to_reparent)} entities\n"
            f"- To Archive: {len(to_archive)} entities\n"
            f"- Already Correct: {len(already_correct)} entities\n\n"
            "If you want to proceed, call program.execute_reconciliation."
        )
        return ReconcileDiffOutput(
            summary=summary,
            to_create_count=len(to_create),
            to_reparent_count=len(to_reparent),
            to_archive_count=len(to_archive),
            already_correct_count=len(already_correct)
        ).model_dump()

class ExecuteReconciliationInput(BaseModel):
    run_id: str = Field(description="The UUID of the hydration run.")

class ExecuteReconciliationOutput(BaseModel):
    status: str
    message: str

class ExecuteReconciliationTool(Tool):
    name = "program.execute_reconciliation"
    description = "Executes the reconciliation diff (archives, reparents, creates) for a given run_id."
    input_schema = ExecuteReconciliationInput
    output_schema = ExecuteReconciliationOutput
    mutates = True
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        run_id = input_data["run_id"]
        import httpx
        
        api_url = os.environ.get("API_URL", "http://localhost:8000")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{api_url}/v1/work_items/reconciliation/{run_id}/execute",
                    headers={"Authorization": f"Bearer dev_{context.tenant_id}"}
                )
                resp.raise_for_status()
                return ExecuteReconciliationOutput(
                    status="started",
                    message=f"Reconciliation engine triggered for run {run_id}."
                ).model_dump()
        except Exception as e:
            return {"error": f"Failed to trigger reconciliation engine: {e}"}

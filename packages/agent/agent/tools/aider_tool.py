import os
import uuid
import subprocess
import logging
import asyncio
from typing import Any
from pydantic import BaseModel, Field

from agent.tools.context import AgentContext
from agent.tools.registry import Tool

logger = logging.getLogger(__name__)

class AiderInvokeInput(BaseModel):
    prompt: str = Field(description="The exact instructions for Aider, including the path to the spec file.")
    working_directory: str = Field(default=".", description="The root directory of the codebase.")

class AiderInvokeOutput(BaseModel):
    success: bool
    status: str
    job_id: str
    log_file: str

async def _run_aider_background(job_id: str, command: list[str], cwd: str, log_file: str):
    logger.info(f"Starting Aider background job {job_id}")
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"--- AIDER JOB {job_id} STARTED ---\n")
            f.write(f"Command: {' '.join(command)}\n\n")
            
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                stdout=f,
                stderr=subprocess.STDOUT
            )
            
            await process.wait()
            
            f.write(f"\n--- AIDER JOB {job_id} COMPLETED WITH CODE {process.returncode} ---\n")
            
    except Exception as e:
        logger.error(f"Aider background job {job_id} failed: {e}")
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n--- AIDER JOB {job_id} FAILED: {e} ---\n")
        except:
            pass

class AiderInvokeTool(Tool):
    name = "aider.invoke"
    description = "Triggers the Aider headless AI software engineer to autonomously write and commit code in the background."
    input_schema = AiderInvokeInput
    output_schema = AiderInvokeOutput
    mutates = True
    requires_approval = True  # We want human approval before the AI starts coding!

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        prompt = input_data["prompt"]
        cwd = input_data.get("working_directory", ".")
        job_id = str(uuid.uuid4())
        
        log_dir = os.path.join(cwd, ".aider.runs")
        log_file = os.path.join(log_dir, f"{job_id}.log")
        
        command = [
            "aider", 
            "--message", prompt,
            "--yes"
        ]
        
        # Fire and forget
        asyncio.create_task(_run_aider_background(job_id, command, cwd, log_file))
        
        return AiderInvokeOutput(
            success=True,
            status="Background job started successfully.",
            job_id=job_id,
            log_file=log_file
        ).model_dump()

class AiderCheckStatusInput(BaseModel):
    job_id: str = Field(description="The UUID of the background Aider job to check.")
    working_directory: str = Field(default=".", description="The root directory of the codebase.")

class AiderCheckStatusOutput(BaseModel):
    success: bool
    status: str
    log_tail: str

class AiderCheckStatusTool(Tool):
    name = "aider.check_status"
    description = "Checks the status and reads the log tail of a background Aider job."
    input_schema = AiderCheckStatusInput
    output_schema = AiderCheckStatusOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        job_id = input_data["job_id"]
        cwd = input_data.get("working_directory", ".")
        log_file = os.path.join(cwd, ".aider.runs", f"{job_id}.log")
        
        if not os.path.exists(log_file):
            return {"success": False, "status": "Not Found", "log_tail": "Log file not found."}
            
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            status = "Running"
            if f"--- AIDER JOB {job_id} COMPLETED" in content:
                status = "Completed"
            elif f"--- AIDER JOB {job_id} FAILED" in content:
                status = "Failed"
                
            tail = content[-2000:] if len(content) > 2000 else content
            
            return {
                "success": True,
                "status": status,
                "log_tail": tail
            }
        except Exception as e:
            return {"success": False, "status": "Error", "log_tail": str(e)}

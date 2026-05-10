import subprocess
import logging
from typing import Any
from pydantic import BaseModel, Field

from agent.tools.context import AgentContext
from agent.tools.registry import Tool

class AiderInvokeInput(BaseModel):
    prompt: str = Field(description="The exact instructions for Aider, including the path to the spec file.")
    working_directory: str = Field(default=".", description="The root directory of the codebase.")

class AiderInvokeOutput(BaseModel):
    success: bool
    cli_output: str

class AiderInvokeTool(Tool):
    name = "aider.invoke"
    description = "Triggers the Aider headless AI software engineer to autonomously write and commit code based on a specification."
    input_schema = AiderInvokeInput
    output_schema = AiderInvokeOutput
    mutates = True
    requires_approval = True  # We want human approval before the AI starts coding!

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        prompt = input_data["prompt"]
        cwd = input_data.get("working_directory", ".")
        
        # We assume Aider is installed and available in the PATH
        command = [
            "aider", 
            "--message", prompt,
            "--yes" # Automatically accept and commit changes
        ]
        
        try:
            # We spin up the Aider sub-process. 
            import asyncio
            
            # Using asyncio to prevent blocking the event loop
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait up to 10 minutes
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)
                return AiderInvokeOutput(
                    success=(process.returncode == 0),
                    cli_output=(stdout.decode() if process.returncode == 0 else stderr.decode())
                ).model_dump()
            except asyncio.TimeoutError:
                process.kill()
                return {"success": False, "cli_output": "Aider timed out after 10 minutes."}
                
        except Exception as e:
            logging.error(f"Failed to invoke Aider: {e}")
            return {"success": False, "cli_output": str(e)}

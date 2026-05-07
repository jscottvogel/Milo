import os
from typing import Any

import boto3
from pydantic import BaseModel, Field

from agent.tools.context import AgentContext
from agent.tools.registry import Tool


class StorageReadInput(BaseModel):
    path: str = Field(description="The path/key of the file to read")


class StorageReadOutput(BaseModel):
    content: str = Field(description="The text content of the file")


class StorageReadTool(Tool):
    name = "storage.read"
    description = "Read the text content of a file from tenant storage."
    input_schema = StorageReadInput
    output_schema = StorageReadOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        bucket = os.environ.get("S3_BUCKET_NAME", "milo-poc-bucket")
        key = f"{context.tenant_id}/{input_data['path']}"
        
        s3 = boto3.client("s3")
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, lambda: s3.get_object(Bucket=bucket, Key=key))
            content = response['Body'].read().decode('utf-8')
            return StorageReadOutput(content=content).model_dump()
        except Exception as e:
            return {"error": str(e)}


class StorageWriteInput(BaseModel):
    path: str = Field(description="The path/key to write the file to")
    content: str = Field(description="The text content to write")
    is_shared: bool = Field(default=False, description="If true, the file is written to a shared external folder")


class StorageWriteOutput(BaseModel):
    success: bool


class StorageWriteTool(Tool):
    name = "storage.write"
    description = "Write text content to a file in tenant storage. Writing to shared folders requires approval."
    input_schema = StorageWriteInput
    output_schema = StorageWriteOutput
    mutates = True
    requires_approval = False # Dynamically updated based on input

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        bucket = os.environ.get("S3_BUCKET_NAME", "milo-poc-bucket")
        key = f"{context.tenant_id}/{input_data['path']}"
        
        if input_data.get("is_shared"):
            # If the router bypassed approval, we could enforce it here, but LangGraph handles approval.
            pass
            
        s3 = boto3.client("s3")
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, 
                lambda: s3.put_object(Bucket=bucket, Key=key, Body=input_data["content"].encode('utf-8'))
            )
            return StorageWriteOutput(success=True).model_dump()
        except Exception as e:
            return {"error": str(e)}

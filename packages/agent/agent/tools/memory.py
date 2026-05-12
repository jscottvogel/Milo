import uuid
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select

from db.models.memory import MemoryChunk
from agent.llm.bedrock import BedrockClient
from agent.tools.context import AgentContext
from agent.tools.registry import Tool


class MemorySearchInput(BaseModel):
    query: str = Field(description="The natural language query to search memory for")
    limit: int = Field(default=5, description="Maximum number of results to return")


class MemorySearchOutput(BaseModel):
    results: list[dict[str, Any]]


class MemorySearchTool(Tool):
    name = "memory__search"
    description = "Search episodic memory using semantic vector search. Use this to recall past events, facts, or context for the current tenant."
    input_schema = MemorySearchInput
    output_schema = MemorySearchOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        query = input_data["query"]
        limit = min(input_data.get("limit", 5), 20)

        # 1. Embed query
        bedrock = BedrockClient()
        query_embedding = await bedrock.embed_text(query)

        # 2. Vector search in DB
        # We need to filter by tenant_id (RLS applies, but we must be explicit or let RLS handle it)
        # Assuming RLS handles it since we are in db_session with tenant_id set
        stmt = select(MemoryChunk).order_by(MemoryChunk.embedding.cosine_distance(query_embedding)).limit(limit)
        
        chunks = context.session.scalars(stmt).all()

        results = []
        for chunk in chunks:
            results.append({
                "kind": chunk.kind,
                "content": chunk.content,
                "metadata": chunk.metadata_jsonb
            })

        return MemorySearchOutput(results=results).model_dump()


class MemoryWriteInput(BaseModel):
    kind: str = Field(description="The kind of memory being written (e.g., 'event', 'decision', 'fact')")
    content: str = Field(description="The detailed content of the memory")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional metadata to attach to the memory")
    work_item_id: str | None = Field(default=None, description="Optional UUID of the work item this memory is associated with")


class MemoryWriteOutput(BaseModel):
    id: str = Field(description="The ID of the newly created memory chunk")


class MemoryWriteTool(Tool):
    name = "memory__write"
    description = "Write a new chunk to episodic memory. Use this to record important events, decisions, or facts that should be remembered."
    input_schema = MemoryWriteInput
    output_schema = MemoryWriteOutput
    mutates = True
    requires_approval = False # Audit-only mutation

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        content = input_data["content"]
        kind = input_data["kind"]
        metadata = input_data.get("metadata", {})
        work_item_id_str = input_data.get("work_item_id")
        
        work_item_id = uuid.UUID(work_item_id_str) if work_item_id_str else None

        # 1. Embed content
        bedrock = BedrockClient()
        embedding = await bedrock.embed_text(content)

        # 2. Insert into DB
        chunk = MemoryChunk(
            tenant_id=uuid.UUID(context.tenant_id),
            work_item_id=work_item_id,
            kind=kind,
            content=content,
            embedding=embedding,
            metadata_jsonb=metadata
        )
        context.session.add(chunk)
        context.session.commit()

        return MemoryWriteOutput(id=str(chunk.id)).model_dump()

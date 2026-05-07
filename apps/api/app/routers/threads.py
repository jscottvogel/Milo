import json

from agent.runner import AgentRunner
from app.middleware.auth import RequestContext
from db.models import Thread
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/v1/threads", tags=["threads"])

class MessageRequest(BaseModel):
    content: str

@router.post("/{id}/messages")
async def create_message(request: Request, id: str, payload: MessageRequest):
    """
    Handles streaming the agent response back to the client via SSE.
    """
    context: RequestContext = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = getattr(request.state, "db", None)
    if not db:
        raise HTTPException(status_code=500, detail="Database session not found")

    # Check if thread exists
    thread = db.query(Thread).filter(Thread.id == id).first()
    if not thread:
        # Create it if it doesn't exist for the PoC
        thread = Thread(id=id, tenant_id=context.tenant_id, status="active")
        db.add(thread)
        db.commit()

    runner = AgentRunner(session=db, tenant_id=context.tenant_id, thread_id=id)

    async def sse_generator():
        try:
            async for event in runner.run_turn(payload.content):
                # We yield SSE formatted messages
                yield {
                    "event": "message",
                    "data": json.dumps(event)
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(sse_generator())

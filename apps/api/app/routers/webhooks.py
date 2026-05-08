import logging
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.models.identity import Tenant, Milo
from agent.runner import AgentRunner
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/webhooks", tags=["Webhooks"])

async def process_nylas_webhook(payload: dict):
    # This background task spins up Milo to process the incoming email/event
    # 1. We need a DB connection. Since this is a background task, we create a new session
    # We must construct a session locally since we are in a background task
    import os
    from sqlalchemy import create_engine
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/milo")
    engine = create_engine(db_url)
    
    # In a real app we'd look up the tenant via the payload's grant_id.
    # For PoC, we take the first tenant.
    try:
        with Session(engine) as db:
            tenant = db.execute(select(Tenant)).scalar_one_or_none()
            if not tenant:
                return
            milo = db.execute(select(Milo).where(Milo.tenant_id == tenant.id)).scalar_one_or_none()
            if not milo:
                return
                
            runner = AgentRunner(
                session=db,
                tenant_id=str(tenant.id),
                thread_id=str(uuid.uuid4()),
                milo_id=str(milo.id)
            )
            
            # 2. Extract Data
            data = payload.get("data", {})
            trigger_type = payload.get("type", "unknown")
            
            if trigger_type == "message.created":
                subject = data.get("object", {}).get("subject", "No Subject")
                snippet = data.get("object", {}).get("snippet", "")
                
                prompt = f"[SYSTEM NOTIFICATION - NYLAS WEBHOOK] New email received.\nSubject: {subject}\nBody: {snippet}\nPlease review and take action."
                
                logger.info("Waking up Milo via Nylas Webhook...")
                async for event in runner.run_turn(prompt):
                    if event["type"] == "tool_use_start":
                        logger.info(f"Milo is using tool: {event['name']}")
                        
            elif trigger_type == "event.created":
                title = data.get("object", {}).get("title", "No Title")
                prompt = f"[SYSTEM NOTIFICATION - NYLAS WEBHOOK] New calendar event created: {title}. Please review."
                async for event in runner.run_turn(prompt):
                    pass
                    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")

@router.get("/nylas")
def verify_nylas_webhook(challenge: str):
    """Nylas sends a GET request with a challenge parameter to verify the webhook."""
    # Return raw text of the challenge
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=challenge)

@router.post("/nylas")
async def receive_nylas_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive Nylas webhook events."""
    payload = await request.json()
    logger.info(f"Received Nylas webhook: {payload.get('type')}")
    
    # Offload processing to a background task so we return 200 OK to Nylas immediately
    background_tasks.add_task(process_nylas_webhook, payload)
    
    return {"status": "ok"}

import asyncio
import os
import sys
import uuid
import logging

# Add the packages/agent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from agent.runner import AgentRunner
from agent.tools.email import EmailReadTool
from agent.tools.context import AgentContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def poll_inbox():
    # Setup DB
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/milo")
    engine = create_engine(db_url)
    
    # We need a valid tenant ID to monitor. For the PoC, we will use the first tenant we find.
    from db.models.identity import Tenant, Milo
    
    with Session(engine) as session:
        tenant = session.query(Tenant).first()
        if not tenant:
            logger.error("No tenant found in the database. Exiting.")
            return
            
        milo = session.query(Milo).filter_by(tenant_id=tenant.id).first()
        if not milo:
            logger.error("No Milo instance found for tenant. Exiting.")
            return

        tenant_id = str(tenant.id)
        milo_id = str(milo.id)
        
        # We generate a generic thread for background processing
        thread_id = str(uuid.uuid4())
        
        runner = AgentRunner(
            session=session,
            tenant_id=tenant_id,
            thread_id=thread_id,
            milo_id=milo_id
        )
        
        context = AgentContext(
            session=session,
            tenant_id=tenant_id,
            milo_id=milo_id,
            thread_id=thread_id,
            integration_tokens=runner.integration_tokens
        )
        
        email_read_tool = EmailReadTool()

        logger.info(f"Starting Email Polling for Tenant: {tenant_id}")
        
        while True:
            logger.info("Polling for new emails...")
            try:
                # 1. Fetch unread emails
                result = await email_read_tool.invoke({"query": "UNSEEN", "limit": 5, "mark_read": True}, context)
                
                if isinstance(result, dict) and "error" in result:
                    logger.error(f"Error fetching emails: {result['error']}")
                elif isinstance(result, dict) and "emails" in result:
                    emails = result["emails"]
                    if not emails:
                        logger.info("No new emails found.")
                    else:
                        for email in emails:
                            logger.info(f"New email from {email['from']}: {email['subject']}")
                            
                            # 2. Trigger Milo autonomously
                            prompt = f"[SYSTEM NOTIFICATION] You have received a new email from {email['from']}. Subject: {email['subject']}. Thread ID: {email['thread_id']}.\n\nBody:\n{email['body']}\n\nPlease review this email. If it is an update or a decision, update the relevant work items. If a reply is needed, draft a reply."
                            
                            logger.info("Waking up Milo...")
                            async for event in runner.run_turn(prompt):
                                if event["type"] == "token":
                                    print(event["content"], end="", flush=True)
                                elif event["type"] == "tool_use_start":
                                    print(f"\n[Milo is using tool: {event['name']}]")
                            print("\n--- Milo processing complete ---")
                
            except Exception as e:
                logger.error(f"Polling loop encountered an error: {e}")
                
            # For testing/PoC purposes, sleep 10 seconds so we can see it act immediately
            logger.info("Sleeping for 10 seconds...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(poll_inbox())

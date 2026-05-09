import os
import uuid
import logging
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# We assume that db and agent packages are installed/accessible in the Lambda environment
from db.models.identity import Tenant, Milo, User, Membership
from db.models.agent import Thread
from agent.runner import AgentRunner
from agent.tools.registry import registry

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    
    tenant_id = event.get("tenant_id")
    if not tenant_id:
        logger.error("No tenant_id provided in event")
        return {"statusCode": 400, "body": "tenant_id is required"}
        
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable is missing")
        return {"statusCode": 500, "body": "Configuration error"}
        
    engine = create_engine(db_url)
    
    try:
        with Session(engine) as db:
            tenant = db.get(Tenant, uuid.UUID(tenant_id))
            if not tenant:
                logger.error(f"Tenant {tenant_id} not found")
                return {"statusCode": 404, "body": "Tenant not found"}
                
            milo = db.execute(select(Milo).where(Milo.tenant_id == tenant.id)).scalar_one_or_none()
            if not milo:
                logger.error(f"Milo configuration for tenant {tenant_id} not found")
                return {"statusCode": 404, "body": "Milo config not found"}
                
            if not milo.briefing_enabled:
                logger.info(f"Briefing is disabled for tenant {tenant_id}")
                return {"statusCode": 200, "body": "Briefing is disabled"}
                
            # Find owner to get their name and email
            owner_membership = db.scalars(select(Membership).where(
                Membership.tenant_id == tenant.id,
                Membership.role == "owner"
            )).first()
            
            if not owner_membership:
                logger.error(f"No owner found for tenant {tenant_id}")
                return {"statusCode": 404, "body": "Owner not found"}
                
            owner = db.get(User, owner_membership.user_id)
            if not owner:
                return {"statusCode": 404, "body": "Owner user not found"}
                
            owner_name = owner.full_name.split()[0] if owner.full_name else "there"
            owner_email = owner.email
            
            logger.info(f"Starting Morning Briefing for tenant {tenant.id}, sending to {owner_email}")
            
            new_thread_id = uuid.uuid4()
            new_thread = Thread(
                id=new_thread_id,
                tenant_id=tenant.id,
                milo_id=milo.id,
                summary="Proactive Morning Briefing"
            )
            db.add(new_thread)
            db.commit()

            runner = AgentRunner(
                session=db,
                tenant_id=str(tenant.id),
                thread_id=str(new_thread_id),
                milo_id=str(milo.id)
            )
            
            # The prompt string exactly following the spec
            prompt = f"""PROACTIVE TRIGGER: Please run your morning briefing routine for {owner_name}.
            
1. Read unread emails using email.read.
2. Read today's and next 7 days calendar using calendar.read.
3. Read open work items (risks, overdue tasks, upcoming milestones) using work_item.read.
4. Evaluate all trigger rules using trigger.evaluate.
5. Compose a structured daily briefing EXACTLY in the following format:

Good morning {owner_name},

📬 INBOX — X unread emails
• [Sender]: [Subject] — [1-line summary]

📅 TODAY — [Day, Date]
• [Time] — [Event Title] ([Meeting link if present])

🗓 THIS WEEK
• [Date] — [Event Title]

⚠ RISKS & BLOCKERS
• [Work item] — [Risk/issue summary]

✅ APPROVALS PENDING — X items
• [Item] — [Approve link]

🏁 UPCOMING MILESTONES
• [Milestone] — due [Date] — [Status]

— Milo

6. Send this briefing via email to '{owner_email}' using email.send.
7. Verify the email was successfully delivered by querying the Sent folder (e.g. "Sent" or "[Gmail]/Sent Mail") using email.read. If it cannot be verified, flag it in the memory entry.
8. Write a memory entry confirming the briefing was sent (and verified) using memory.store with kind="event".
"""
            
            # In a lambda, we need to run asyncio event loop to consume the async generator
            import asyncio
            async def run_agent():
                async for event in runner.run_turn(prompt):
                    pass
            
            asyncio.run(run_agent())
            
            return {"statusCode": 200, "body": "Briefing sent successfully"}
            
    except Exception as e:
        logger.error(f"Error in morning briefing lambda: {e}", exc_info=True)
        return {"statusCode": 500, "body": str(e)}

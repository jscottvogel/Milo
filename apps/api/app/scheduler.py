import os
import uuid
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select

from db.models.identity import Tenant, Milo
from db.models.agent import Thread
from agent.runner import AgentRunner
from agent.tools.registry import registry
from agent.tools.context import AgentContext

logger = logging.getLogger(__name__)

# Note: APScheduler requires a timezone.
scheduler = AsyncIOScheduler(timezone="UTC")

async def run_morning_briefing():
    logger.info("Running Morning Briefing for all tenants...")
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/milo")
    engine = create_engine(db_url)
    
    try:
        with Session(engine) as db:
            tenants = db.execute(select(Tenant)).scalars().all()
            for tenant in tenants:
                milo = db.execute(select(Milo).where(Milo.tenant_id == tenant.id)).scalar_one_or_none()
                if not milo:
                    continue
                
                logger.info(f"Starting Morning Briefing for tenant {tenant.id}")
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
                
                prompt = (
                    "PROACTIVE TRIGGER: Please run your morning briefing routine. "
                    "1. Call email.read to check for unread emails. "
                    "2. Call calendar.read for today's and tomorrow's events. "
                    "3. Call work_item.read to surface overdue tasks and upcoming milestones. "
                    "4. Call memory.search for any pending action items or flagged risks. "
                    "5. Compose a structured daily briefing and send it via email.send to 'j_scott_vogel@yahoo.com'. "
                    "6. Write a memory entry confirming the briefing was sent."
                )
                
                # Consume the generator to allow the agent to run completely
                async for event in runner.run_turn(prompt):
                    pass
    except Exception as e:
        logger.error(f"Error in morning briefing: {e}")

async def evaluate_triggers():
    logger.info("Evaluating triggers for all tenants...")
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/milo")
    engine = create_engine(db_url)
    
    try:
        with Session(engine) as db:
            tenants = db.execute(select(Tenant)).scalars().all()
            for tenant in tenants:
                milo = db.execute(select(Milo).where(Milo.tenant_id == tenant.id)).scalar_one_or_none()
                if not milo:
                    continue
                
                logger.info(f"Evaluating triggers for tenant {tenant.id}")
                # Create a temporary runner just to extract integration tokens
                runner_for_tokens = AgentRunner(
                    session=db,
                    tenant_id=str(tenant.id),
                    thread_id="",
                    milo_id=str(milo.id)
                )
                context = AgentContext(
                    session=db,
                    tenant_id=str(tenant.id),
                    milo_id=str(milo.id),
                    thread_id=str(uuid.uuid4()),
                    integration_tokens=runner_for_tokens.integration_tokens
                )
                
                trigger_tool = registry.get_tool("trigger.evaluate")
                if trigger_tool:
                    await trigger_tool.invoke({}, context)
    except Exception as e:
        logger.error(f"Error evaluating triggers: {e}")

def start_scheduler():
    # Morning briefing at 7:00 AM daily
    morning_time = os.environ.get("SCHEDULE_MORNING_BRIEFING", "07:00")
    if ":" in morning_time:
        morning_hour, morning_minute = morning_time.split(":")
        scheduler.add_job(
            run_morning_briefing,
            CronTrigger(hour=int(morning_hour), minute=int(morning_minute)),
            id="morning_briefing",
            replace_existing=True
        )
    
    # Triggers evaluation (e.g. every hour)
    eval_cron = os.environ.get("SCHEDULE_EVALUATE_TRIGGERS", "0 * * * *")  # top of the hour
    parts = eval_cron.split()
    if len(parts) == 5:
        scheduler.add_job(
            evaluate_triggers,
            CronTrigger(minute=parts[0], hour=parts[1], day=parts[2], month=parts[3], day_of_week=parts[4]),
            id="evaluate_triggers",
            replace_existing=True
        )
        
    scheduler.start()
    logger.info("APScheduler started")

def stop_scheduler():
    scheduler.shutdown()
    logger.info("APScheduler stopped")

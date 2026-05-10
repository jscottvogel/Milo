import os
import uuid
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select

from db.models.identity import Tenant, Milo
from db.models.agent import Thread
from agent.runner import AgentRunner
from agent.tools.registry import registry
from agent.tools.context import AgentContext

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.config import settings

logger = logging.getLogger(__name__)

# Note: APScheduler requires a timezone.
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)

jobstores = {
    'default': SQLAlchemyJobStore(url=db_url)
}
scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="America/Chicago")


async def evaluate_triggers():
    logger.info("Evaluating hourly triggers for all tenants...")
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"): db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql+asyncpg://"): db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    engine = create_engine(db_url)
    
    try:
        with Session(engine) as db:
            tenants = db.execute(select(Tenant)).scalars().all()
            for tenant in tenants:
                milo = db.execute(select(Milo).where(Milo.tenant_id == tenant.id)).scalar_one_or_none()
                if not milo:
                    continue
                
                logger.info(f"Executing autonomous hourly background run for tenant {tenant.id}")
                
                thread_id = str(uuid.uuid4())
                thread = Thread(id=uuid.UUID(thread_id), tenant_id=tenant.id, milo_id=milo.id, summary="Hourly Health Check Autonomous Run")
                db.add(thread)
                db.commit()
                
                runner = AgentRunner(
                    session=db,
                    tenant_id=str(tenant.id),
                    thread_id=thread_id,
                    milo_id=str(milo.id)
                )
                
                # Check config
                context = AgentContext(
                    session=db,
                    tenant_id=str(tenant.id),
                    milo_id=str(milo.id),
                    thread_id=runner.thread_id,
                    integration_tokens=runner.integration_tokens
                )
                
                is_enabled = True
                storage_tool = registry.get_tool("storage.read")
                if storage_tool:
                    try:
                        res = await storage_tool.invoke({"path": "config/scheduler.json"}, context)
                        if isinstance(res, dict) and "content" in res:
                            import json
                            config = json.loads(res["content"])
                            if "hourly_health_check" in config:
                                is_enabled = config["hourly_health_check"].get("enabled", True)
                    except Exception as e:
                        logger.warning(f"Could not read config/scheduler.json: {e}")
                        
                if not is_enabled:
                    logger.info(f"Hourly health check disabled for tenant {tenant.id}")
                    continue
                
                await runner.run_autonomous_turn("Hourly Health Check. Evaluate triggers, check overdue tasks, and act if rules fire.")
    except Exception as e:
        logger.error(f"Error evaluating triggers: {e}")

async def run_weekly_review():
    logger.info("Executing Weekly Review for all tenants...")
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"): db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql+asyncpg://"): db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    engine = create_engine(db_url)
    
    try:
        with Session(engine) as db:
            tenants = db.execute(select(Tenant)).scalars().all()
            for tenant in tenants:
                milo = db.execute(select(Milo).where(Milo.tenant_id == tenant.id)).scalar_one_or_none()
                if not milo:
                    continue
                
                logger.info(f"Executing autonomous weekly review run for tenant {tenant.id}")
                
                thread_id = str(uuid.uuid4())
                thread = Thread(id=uuid.UUID(thread_id), tenant_id=tenant.id, milo_id=milo.id, summary="Weekly Review Autonomous Run")
                db.add(thread)
                db.commit()
                
                runner = AgentRunner(
                    session=db,
                    tenant_id=str(tenant.id),
                    thread_id=thread_id,
                    milo_id=str(milo.id)
                )
                
                # Check config
                context = AgentContext(
                    session=db,
                    tenant_id=str(tenant.id),
                    milo_id=str(milo.id),
                    thread_id=runner.thread_id,
                    integration_tokens=runner.integration_tokens
                )
                
                is_enabled = True
                storage_tool = registry.get_tool("storage.read")
                if storage_tool:
                    try:
                        res = await storage_tool.invoke({"path": "config/scheduler.json"}, context)
                        if isinstance(res, dict) and "content" in res:
                            import json
                            config = json.loads(res["content"])
                            if "stale_program_scan" in config:
                                is_enabled = config["stale_program_scan"].get("enabled", True)
                    except Exception as e:
                        logger.warning(f"Could not read config/scheduler.json: {e}")
                        
                if not is_enabled:
                    logger.info(f"Stale program scan disabled for tenant {tenant.id}")
                    continue
                
                await runner.run_autonomous_turn("Stale Program Daily Scan. Scan active programs for 7+ days inactivity and send a nudge email.")
    except Exception as e:
        logger.error(f"Error evaluating weekly review: {e}")

async def run_morning_briefing():
    logger.info("Executing Morning Briefing for all tenants...")
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"): db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql+asyncpg://"): db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    engine = create_engine(db_url)
    
    try:
        with Session(engine) as db:
            tenants = db.execute(select(Tenant)).scalars().all()
            for tenant in tenants:
                milo = db.execute(select(Milo).where(Milo.tenant_id == tenant.id)).scalar_one_or_none()
                if not milo or not getattr(milo, 'briefing_enabled', True):
                    logger.info(f"Morning briefing disabled for tenant {tenant.id}")
                    continue
                
                logger.info(f"Executing morning briefing for tenant {tenant.id}")
                
                thread_id = str(uuid.uuid4())
                thread = Thread(id=uuid.UUID(thread_id), tenant_id=tenant.id, milo_id=milo.id, summary="Morning Briefing Autonomous Run")
                db.add(thread)
                db.commit()
                
                runner = AgentRunner(
                    session=db,
                    tenant_id=str(tenant.id),
                    thread_id=thread_id,
                    milo_id=str(milo.id)
                )
                
                prompt = (
                    "It is time for the Morning Briefing. Please do the following:\n"
                    "1. Call email.read for unread emails.\n"
                    "2. Call calendar.read for today and tomorrow.\n"
                    "3. Call work_item.read for overdue and upcoming work items.\n"
                    "4. Call memory.search for pending action items or flagged risks.\n"
                    "5. Compose a structured daily briefing and send it using push.notify to j_scott_vogel@yahoo.com.\n"
                    "6. Write a memory entry confirming the morning briefing was sent today."
                )
                await runner.run_autonomous_turn(prompt)
    except Exception as e:
        logger.error(f"Error executing morning briefing: {e}")

async def run_hourly_monitor():
    logger.info("Executing Hourly Program Monitor for all tenants...")
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"): db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql+asyncpg://"): db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    engine = create_engine(db_url)
    
    try:
        with Session(engine) as db:
            tenants = db.execute(select(Tenant)).scalars().all()
            for tenant in tenants:
                milo = db.execute(select(Milo).where(Milo.tenant_id == tenant.id)).scalar_one_or_none()
                if not milo or not getattr(milo, 'hourly_monitor_enabled', True):
                    logger.info(f"Hourly monitor disabled for tenant {tenant.id}")
                    continue
                
                logger.info(f"Executing hourly monitor for tenant {tenant.id}")
                
                thread_id = str(uuid.uuid4())
                thread = Thread(id=uuid.UUID(thread_id), tenant_id=tenant.id, milo_id=milo.id, summary="Hourly Monitor Autonomous Run")
                db.add(thread)
                db.commit()
                
                runner = AgentRunner(
                    session=db,
                    tenant_id=str(tenant.id),
                    thread_id=thread_id,
                    milo_id=str(milo.id)
                )
                
                prompt = (
                    "Autonomous Trigger: It is time for the Hourly Program Monitor & Engineering Handoff loop. Please strictly follow these steps:\n"
                    "1. Use work_item.read to read all root items (include_children: true) and identify overdue tasks, stalled milestones, unresolved risks, and missing owners.\n"
                    "2. Use memory.search to audit the current capability map against confirmed COMPLETED_ handoffs. Identify any capability that is missing or not yet handed off.\n"
                    "3. For each gap identified:\n"
                    "   a. Use memory.search to check if an idempotency key like 'hourly_handoff_{capability_slug}_{YYYY-MM-DD}' exists. If it exists in the last 24 hours, SKIP IT.\n"
                    "   b. If new, use developer.handoff to generate a structured requirements doc. Also use storage.write to save a copy to 'engineering_requests/{slug}.md'.\n"
                    "   c. Use email.send to send the full handoff spec to j_scott_vogel@yahoo.com with the subject: '[Milo Handoff] {capability name} — {date}'.\n"
                    "   d. Use memory.write to write an 'event' memory entry recording the gap identified, handoff filed, timestamp, and the exact idempotency key used in step 3a.\n"
                    "Do not output any chat messages or push notifications unless a new handoff is filed."
                )
                await runner.run_autonomous_turn(prompt)
    except Exception as e:
        logger.error(f"Error executing hourly monitor: {e}")

def start_scheduler():
    # Triggers evaluation (e.g. every hour)
    eval_cron = os.environ.get("SCHEDULE_EVALUATE_TRIGGERS", "0 * * * *")  # Hourly
    parts = eval_cron.split()
    if len(parts) == 5:
        scheduler.add_job(
            evaluate_triggers,
            CronTrigger(minute=parts[0], hour=parts[1], day=parts[2], month=parts[3], day_of_week=parts[4]),
            id="evaluate_triggers",
            replace_existing=True
        )
        
    briefing_cron = os.environ.get("SCHEDULE_MORNING_BRIEFING", "0 7 * * *")
    b_parts = briefing_cron.split()
    if len(b_parts) == 5:
        scheduler.add_job(
            run_morning_briefing,
            CronTrigger(minute=b_parts[0], hour=b_parts[1], day=b_parts[2], month=b_parts[3], day_of_week=b_parts[4]),
            id="morning_briefing",
            replace_existing=True
        )
        
    scheduler.add_job(
        run_weekly_review,
        CronTrigger(day_of_week='mon', hour=9, minute=0),
        id="weekly_review",
        replace_existing=True
    )
        
    scheduler.add_job(
        run_hourly_monitor,
        IntervalTrigger(hours=1),
        id="hourly_monitor",
        name="Hourly Program Monitor",
        replace_existing=True
    )
        
    scheduler.start()
    logger.info("APScheduler started")

def stop_scheduler():
    scheduler.shutdown()
    logger.info("APScheduler stopped")

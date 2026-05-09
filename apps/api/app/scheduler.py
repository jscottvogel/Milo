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


async def evaluate_triggers():
    logger.info("Evaluating hourly triggers for all tenants...")
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/milo")
    engine = create_engine(db_url)
    
    try:
        with Session(engine) as db:
            tenants = db.execute(select(Tenant)).scalars().all()
            for tenant in tenants:
                milo = db.execute(select(Milo).where(Milo.tenant_id == tenant.id)).scalar_one_or_none()
                if not milo:
                    continue
                
                logger.info(f"Executing autonomous hourly background run for tenant {tenant.id}")
                
                runner = AgentRunner(
                    session=db,
                    tenant_id=str(tenant.id),
                    thread_id=str(uuid.uuid4()),
                    milo_id=str(milo.id)
                )
                
                await runner.run_autonomous_turn("Scheduled Hourly Trigger Evaluation")
    except Exception as e:
        logger.error(f"Error evaluating triggers: {e}")

async def run_weekly_review():
    logger.info("Executing Weekly Review for all tenants...")
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/milo")
    engine = create_engine(db_url)
    
    try:
        with Session(engine) as db:
            tenants = db.execute(select(Tenant)).scalars().all()
            for tenant in tenants:
                milo = db.execute(select(Milo).where(Milo.tenant_id == tenant.id)).scalar_one_or_none()
                if not milo:
                    continue
                
                logger.info(f"Executing autonomous weekly review run for tenant {tenant.id}")
                
                runner = AgentRunner(
                    session=db,
                    tenant_id=str(tenant.id),
                    thread_id=str(uuid.uuid4()),
                    milo_id=str(milo.id)
                )
                
                await runner.run_autonomous_turn("Scheduled Weekly Review (Mondays at 9 AM)")
    except Exception as e:
        logger.error(f"Error evaluating weekly review: {e}")

def start_scheduler():
    # Morning briefing is now handled entirely by AWS EventBridge Scheduler.
    # Triggers evaluation (e.g. every hour)
    eval_cron = os.environ.get("SCHEDULE_EVALUATE_TRIGGERS", "0 */4 * * *")  # Every 4 hours
    parts = eval_cron.split()
    if len(parts) == 5:
        scheduler.add_job(
            evaluate_triggers,
            CronTrigger(minute=parts[0], hour=parts[1], day=parts[2], month=parts[3], day_of_week=parts[4]),
            id="evaluate_triggers",
            replace_existing=True
        )
        
    scheduler.add_job(
        run_weekly_review,
        CronTrigger(day_of_week='mon', hour=9, minute=0),
        id="weekly_review",
        replace_existing=True
    )
        
    scheduler.start()
    logger.info("APScheduler started")

def stop_scheduler():
    scheduler.shutdown()
    logger.info("APScheduler stopped")

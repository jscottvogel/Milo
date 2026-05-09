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

def start_scheduler():
    # Morning briefing is now handled entirely by AWS EventBridge Scheduler.
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

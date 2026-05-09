import os
import json
import logging
import asyncio
import uuid
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from db.models.identity import Tenant, Milo
from agent.runner import AgentRunner
from agent.tools.registry import registry
from agent.tools.context import AgentContext

logger = logging.getLogger()
logger.setLevel(logging.INFO)

async def _process_event(tenant_id: str, trigger_type: str):
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL is not set")
        return
        
    engine = create_engine(db_url)
    
    with Session(engine) as db:
        milo = db.execute(select(Milo).where(Milo.tenant_id == tenant_id)).scalar_one_or_none()
        if not milo:
            logger.error(f"No Milo found for tenant {tenant_id}")
            return
            
        runner = AgentRunner(
            session=db,
            tenant_id=tenant_id,
            thread_id=str(uuid.uuid4()),
            milo_id=str(milo.id)
        )
        
        # Check config/scheduler.json via storage tool
        context = AgentContext(
            session=db,
            tenant_id=tenant_id,
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
                    config = json.loads(res["content"])
                    if trigger_type in config:
                        is_enabled = config[trigger_type].get("enabled", True)
            except Exception as e:
                logger.warning(f"Could not read config/scheduler.json: {e}")
                
        if not is_enabled:
            logger.info(f"Trigger {trigger_type} disabled for tenant {tenant_id}")
            return
            
        prompt = f"Autonomous Trigger: {trigger_type}"
        if trigger_type == "morning_briefing":
            prompt = "Daily 7AM Morning Briefing. Read inbox, scan calendar, evaluate trigger rules, check work item statuses, compute critical paths for active programs using program.critical_path (if dependencies changed recently), and email a morning briefing to j_scott_vogel@yahoo.com."
        elif trigger_type == "hourly_health_check":
            prompt = "Hourly Health Check. Evaluate triggers, check overdue tasks, and act if rules fire."
        elif trigger_type == "stale_program_scan":
            prompt = "Stale Program Daily Scan. Scan active programs for 7+ days inactivity and send a nudge email."
            
        await runner.run_autonomous_turn(prompt)

def lambda_handler(event, context):
    """
    EventBridge Target.
    Expected event payload:
    {
      "detail": {
        "tenant_id": "uuid" or "all",
        "trigger_type": "morning_briefing"
      }
    }
    """
    detail = event.get("detail", {})
    tenant_id = detail.get("tenant_id", "all")
    trigger_type = detail.get("trigger_type")
    
    if not trigger_type:
        logger.error("Missing trigger_type in event detail")
        return {"statusCode": 400, "body": "Missing trigger_type"}
        
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return {"statusCode": 500, "body": "Missing DATABASE_URL"}
        
    engine = create_engine(db_url)
    with Session(engine) as db:
        if tenant_id == "all":
            tenants = db.execute(select(Tenant)).scalars().all()
            for tenant in tenants:
                asyncio.run(_process_event(str(tenant.id), trigger_type))
        else:
            asyncio.run(_process_event(tenant_id, trigger_type))
            
    return {"statusCode": 200, "body": "Success"}

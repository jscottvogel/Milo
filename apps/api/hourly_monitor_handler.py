"""Hourly Autonomous Program Monitor Lambda Handler.

This is a SEPARATE Lambda from the daily briefing Lambda. It is triggered by a
dedicated EventBridge Scheduler rule every 60 minutes and autonomously:
  1. Reads all root work items with children to identify health issues.
  2. Audits capability gaps against confirmed COMPLETED_ handoffs.
  3. For each new gap (idempotency-checked), files a developer handoff,
     calls implement_feature, and emails j_scott_vogel@yahoo.com.
  4. Writes a memory event entry for each gap processed.

Do NOT modify this file to add daily briefing logic.
Do NOT call aider__invoke anywhere in this module.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from agent.runner import AgentRunner
from agent.tools.context import AgentContext
from agent.tools.registry import registry
from db.models.agent import Thread
from db.models.identity import Milo, Tenant

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HANDOFF_EMAIL = "j_scott_vogel@yahoo.com"
IDEMPOTENCY_WINDOW_HOURS = 24

HOURLY_MONITOR_PROMPT = (
    "Autonomous Trigger: It is time for the Hourly Program Monitor & Engineering Handoff loop. "
    "Do NOT call aider__invoke at any point. "
    "Please strictly follow these steps:\n"
    "1. Use work_item.read to read all root items (include_children: true) and identify "
    "overdue tasks, stalled milestones, unresolved risks, and missing owners.\n"
    "2. Use stakeholder.read to check program stakeholders. Flag stakeholders with "
    "influence=high and satisfaction <= 2 as a risk.\n"
    "3. Use memory.search to audit the current capability map against confirmed COMPLETED_ "
    "handoffs in engineering_requests/. Identify any capability that is missing, not yet "
    "handed off, or handed off but not confirmed live.\n"
    "4. For each gap identified:\n"
    "   a. Use memory.search to check if an idempotency key like "
    "'hourly_handoff_{capability_slug}_{YYYY-MM-DD}' exists within the last 24 hours. "
    "If it exists, SKIP that gap entirely.\n"
    "   b. If the gap is new, use developer.handoff to generate a structured requirements "
    "doc with title, description, acceptance criteria, and technical notes.\n"
    "   c. Use storage.write to save the handoff to engineering_requests/{slug}.md.\n"
    "   d. Use implement_feature with repo_path from the MILO_REPO_PATH environment variable, "
    "feature_prompt = the full handoff spec text, and review_mode=false. "
    "Log the result. If implement_feature returns an error, note the error and fall back "
    "to email-only; do not abort the rest of the flow.\n"
    "   e. Use email.send to email " + HANDOFF_EMAIL + " with subject "
    "'[Milo Handoff] {capability name} — {date}'. The body must include the full spec AND "
    "the implement_feature result (or the error, if it failed).\n"
    "   f. Use memory.write to write an 'event' memory entry recording: the gap name, "
    "timestamp, implement_feature result or error, and the exact idempotency key used in "
    "step 4a.\n"
    "5. Do not output any chat messages or push notifications unless a new handoff is filed.\n"
    "6. At the end, output a JSON summary with keys: "
    "run_id, gaps_found, handoffs_filed, implement_feature_results, emails_sent, skipped."
)


def _get_sync_db_url() -> str:
    """Return a synchronous psycopg database URL regardless of the env var format.

    Justification: Lambda uses a synchronous SQLAlchemy engine; async drivers are not
    needed here and add unnecessary cold-start latency.
    """
    url = os.environ["DATABASE_URL"]
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _build_run_summary(
    run_id: str,
    gaps_found: int,
    handoffs_filed: int,
    implement_feature_results: list[dict[str, Any]],
    emails_sent: int,
    skipped: int,
) -> dict[str, Any]:
    """Construct a structured CloudWatch-friendly run summary.

    Args:
        run_id: Unique identifier for this Lambda invocation.
        gaps_found: Total capability gaps detected before idempotency filtering.
        handoffs_filed: Number of new handoffs actually filed this run.
        implement_feature_results: List of dicts with {capability, status, detail}.
        emails_sent: Number of emails dispatched this run.
        skipped: Number of gaps skipped due to 24-hour idempotency window.

    Returns:
        A dict suitable for JSON serialisation and CloudWatch structured logging.
    """
    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gaps_found": gaps_found,
        "handoffs_filed": handoffs_filed,
        "implement_feature_results": implement_feature_results,
        "emails_sent": emails_sent,
        "skipped": skipped,
    }


async def _process_tenant(
    db: Session,
    tenant: Tenant,
    milo: Milo,
    run_id: str,
) -> dict[str, Any]:
    """Run the hourly monitor logic for a single tenant.

    Creates a dedicated thread, builds an AgentRunner, and executes the
    autonomous prompt. Returns a summary dict for CloudWatch logging.

    Args:
        db: Active SQLAlchemy session with tenant RLS context set.
        tenant: The Tenant ORM instance to process.
        milo: The Milo ORM instance associated with the tenant.
        run_id: The invocation-level run identifier for log correlation.

    Returns:
        A dict with keys matching _build_run_summary output.

    Raises:
        Does not raise; all exceptions are caught and logged so that one tenant
        failure does not abort processing of subsequent tenants.
    """
    logger.info(
        "hourly_monitor.tenant_start",
        extra={"run_id": run_id, "tenant_id": str(tenant.id)},
    )

    thread_id = str(uuid.uuid4())
    thread = Thread(
        id=uuid.UUID(thread_id),
        tenant_id=tenant.id,
        milo_id=milo.id,
        summary="Hourly Monitor Autonomous Run",
    )
    db.add(thread)
    db.commit()

    runner = AgentRunner(
        session=db,
        tenant_id=str(tenant.id),
        thread_id=thread_id,
        milo_id=str(milo.id),
    )

    # Check per-tenant toggle from scheduler config stored in S3/storage
    context = AgentContext(
        session=db,
        tenant_id=str(tenant.id),
        milo_id=str(milo.id),
        thread_id=runner.thread_id,
        integration_tokens=runner.integration_tokens,
    )

    is_enabled = getattr(milo, "hourly_monitor_enabled", True)
    storage_tool = registry.get_tool("storage.read")
    if storage_tool and is_enabled:
        try:
            res = await storage_tool.invoke({"path": "config/scheduler.json"}, context)
            if isinstance(res, dict) and "content" in res:
                config = json.loads(res["content"])
                is_enabled = config.get("hourly_monitor", {}).get("enabled", True)
        except Exception as cfg_err:  # noqa: BLE001
            logger.warning(
                "hourly_monitor.config_read_failed",
                extra={"run_id": run_id, "tenant_id": str(tenant.id), "error": str(cfg_err)},
            )

    if not is_enabled:
        logger.info(
            "hourly_monitor.disabled",
            extra={"run_id": run_id, "tenant_id": str(tenant.id)},
        )
        return _build_run_summary(
            run_id=run_id,
            gaps_found=0,
            handoffs_filed=0,
            implement_feature_results=[],
            emails_sent=0,
            skipped=0,
        )

    # Run the autonomous agent turn
    result_text: str = ""
    try:
        result_text = await runner.run_autonomous_turn(HOURLY_MONITOR_PROMPT)
    except Exception as agent_err:  # noqa: BLE001
        logger.error(
            "hourly_monitor.agent_error",
            extra={"run_id": run_id, "tenant_id": str(tenant.id), "error": str(agent_err)},
        )
        result_text = f"{{\"error\": \"{agent_err}\"}}"

    # Attempt to parse the JSON summary the agent was instructed to produce
    summary: dict[str, Any] = {
        "run_id": run_id,
        "gaps_found": 0,
        "handoffs_filed": 0,
        "implement_feature_results": [],
        "emails_sent": 0,
        "skipped": 0,
    }
    if result_text:
        try:
            # The agent may embed the JSON in prose; try to extract it.
            import re

            json_match = re.search(r"\{[\s\S]*\}", result_text)
            if json_match:
                parsed = json.loads(json_match.group())
                for key in summary:
                    if key in parsed:
                        summary[key] = parsed[key]
        except (json.JSONDecodeError, AttributeError):
            pass  # Non-JSON output is acceptable; we just log what we have

    logger.info(
        "hourly_monitor.tenant_complete",
        extra={"run_id": run_id, "tenant_id": str(tenant.id), **summary},
    )
    return summary


async def _run_all_tenants(run_id: str) -> list[dict[str, Any]]:
    """Iterate over all tenants and run the hourly monitor for each.

    Args:
        run_id: Invocation-level identifier propagated to per-tenant summaries.

    Returns:
        List of per-tenant summary dicts.
    """
    engine = create_engine(_get_sync_db_url())
    results: list[dict[str, Any]] = []

    with Session(engine) as db:
        tenants = db.execute(select(Tenant)).scalars().all()
        for tenant in tenants:
            milo = db.execute(
                select(Milo).where(Milo.tenant_id == tenant.id)
            ).scalar_one_or_none()
            if not milo:
                logger.info(
                    "hourly_monitor.no_milo",
                    extra={"run_id": run_id, "tenant_id": str(tenant.id)},
                )
                continue

            tenant_summary = await _process_tenant(
                db=db, tenant=tenant, milo=milo, run_id=run_id
            )
            results.append(tenant_summary)

    engine.dispose()
    return results


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:  # noqa: ANN401
    """AWS Lambda entry point for the Hourly Program Monitor.

    Triggered by an EventBridge Scheduler rule every 60 minutes. This handler
    is SEPARATE from the daily briefing Lambda; do not merge them.

    Args:
        event: EventBridge Scheduler event payload (not used directly).
        context: AWS Lambda context object (used for request_id logging).

    Returns:
        A dict with statusCode and a JSON-serialisable body containing per-tenant
        run summaries and aggregate CloudWatch metrics.
    """
    run_id = getattr(context, "aws_request_id", str(uuid.uuid4()))
    logger.info(
        "hourly_monitor.invocation_start",
        extra={"run_id": run_id, "event": json.dumps(event)},
    )

    import asyncio

    tenant_results = asyncio.run(_run_all_tenants(run_id))

    # Aggregate metrics for CloudWatch
    total_gaps = sum(r.get("gaps_found", 0) for r in tenant_results)
    total_handoffs = sum(r.get("handoffs_filed", 0) for r in tenant_results)
    total_emails = sum(r.get("emails_sent", 0) for r in tenant_results)
    total_skipped = sum(r.get("skipped", 0) for r in tenant_results)
    all_impl_results: list[dict[str, Any]] = []
    for r in tenant_results:
        all_impl_results.extend(r.get("implement_feature_results", []))

    aggregate_summary = _build_run_summary(
        run_id=run_id,
        gaps_found=total_gaps,
        handoffs_filed=total_handoffs,
        implement_feature_results=all_impl_results,
        emails_sent=total_emails,
        skipped=total_skipped,
    )
    aggregate_summary["tenant_count"] = len(tenant_results)

    logger.info(
        "hourly_monitor.invocation_complete",
        extra=aggregate_summary,
    )

    return {
        "statusCode": 200,
        "body": json.dumps(aggregate_summary),
    }

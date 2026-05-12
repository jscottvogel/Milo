"""Hourly Autonomous Program Monitor Lambda Handler.

This is a SEPARATE Lambda function from the daily morning briefing.
EventBridge Scheduler fires this every 60 minutes.

Run lifecycle
-------------
1.  Read all root work items (include_children=True).
2.  Audit engineering_requests/ storage for COMPLETED_ vs pending handoffs.
3.  Search episodic memory for the 20-capability target list; compare against
    confirmed-live capabilities.
4.  For each gap:
    a.  Check idempotency – skip if filed within the last 24 hours.
    b.  Call developer__handoff to build a structured spec.
    c.  Save spec to engineering_requests/{slug}.md via storage.write.
    d.  Call implement_feature (no review gate) via the MCP feature-implementer
        tool.  Falls back to email-only if the tool errors.
    e.  Email j_scott_vogel@yahoo.com with the full spec + implementation result.
    f.  Write a memory entry recording the event + idempotency key.

CloudWatch log payload per run
-------------------------------
  run_id, gaps_found, handoffs_filed, implement_feature_results,
  emails_sent, skipped
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import date, datetime, timezone
from typing import Any

import boto3
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from db.models.agent import Thread
from db.models.identity import Milo, Tenant
from agent.runner import AgentRunner
from agent.tools.context import AgentContext
from agent.tools.registry import registry

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------

DATABASE_URL: str = os.environ["DATABASE_URL"]
MILO_REPO_PATH: str = os.environ.get("MILO_REPO_PATH", "/var/task")
HANDOFF_EMAIL: str = os.environ.get("HANDOFF_EMAIL", "j_scott_vogel@yahoo.com")

# The 20-capability target list that every Milo deployment should have.
TARGET_CAPABILITIES: list[str] = [
    "work_item_read",
    "work_item_update",
    "memory_search",
    "memory_write",
    "program_read",
    "program_update",
    "email_send",
    "email_read",
    "calendar_read",
    "storage_read",
    "storage_write",
    "stakeholder_read",
    "stakeholder_update",
    "portfolio_read",
    "approval_tools",
    "push_notify",
    "developer_handoff",
    "web_search",
    "slack_integration",
    "github_integration",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise_db_url(url: str) -> str:
    """Convert async/legacy postgres scheme to psycopg (sync)."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return url


def _idempotency_key(capability_slug: str) -> str:
    """Return the idempotency key for a capability on today's date."""
    today = date.today().isoformat()  # YYYY-MM-DD
    return f"hourly_handoff_{capability_slug}_{today}"


def _slug(capability_name: str) -> str:
    """Convert a capability name to a filesystem-safe slug."""
    return capability_name.lower().replace(" ", "_").replace("-", "_")


async def _check_idempotency(
    storage_tool: Any,
    memory_tool: Any,
    context: AgentContext,
    idem_key: str,
) -> bool:
    """Return True if this gap was already filed within the last 24 hours."""
    if memory_tool is None:
        return False
    try:
        result = await memory_tool.invoke(
            {"query": idem_key, "top_k": 3},
            context,
        )
        chunks = result.get("chunks", []) if isinstance(result, dict) else []
        for chunk in chunks:
            content = chunk.get("content", "") if isinstance(chunk, dict) else str(chunk)
            if idem_key in content:
                logger.info("Idempotency hit for key %s – skipping.", idem_key)
                return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Idempotency check failed (will proceed): %s", exc)
    return False


async def _save_handoff(
    storage_tool: Any,
    context: AgentContext,
    slug: str,
    spec_text: str,
) -> None:
    """Persist the handoff spec to engineering_requests/{slug}.md."""
    if storage_tool is None:
        logger.warning("storage.write tool not available; cannot save handoff file.")
        return
    try:
        await storage_tool.invoke(
            {
                "path": f"engineering_requests/{slug}.md",
                "content": spec_text,
            },
            context,
        )
        logger.info("Handoff spec saved to engineering_requests/%s.md", slug)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to save handoff file for %s: %s", slug, exc)


async def _invoke_implement_feature(
    context: AgentContext,
    spec_text: str,
) -> dict[str, Any]:
    """Call the implement_feature MCP tool (no review gate).

    Returns a dict with keys ``status`` and optionally ``summary``/``error``.
    """
    impl_tool = registry.get_tool("implement_feature")
    if impl_tool is None:
        return {"status": "skipped", "reason": "implement_feature tool not registered"}
    try:
        result = await impl_tool.invoke(
            {
                "repo_path": MILO_REPO_PATH,
                "feature_prompt": spec_text,
                "review_mode": False,
            },
            context,
        )
        return result if isinstance(result, dict) else {"status": "applied", "raw": str(result)}
    except Exception as exc:  # noqa: BLE001
        logger.error("implement_feature errored for spec; falling back to email-only: %s", exc)
        return {"status": "error", "error": str(exc)}


async def _send_email(
    email_tool: Any,
    context: AgentContext,
    capability_name: str,
    spec_text: str,
    impl_result: dict[str, Any],
) -> bool:
    """Email the handoff spec + implementation result.  Returns True on success."""
    if email_tool is None:
        logger.warning("email.send tool not available; cannot send handoff email.")
        return False
    today_str = date.today().isoformat()
    subject = f"[Milo Handoff] {capability_name} — {today_str}"
    impl_section = json.dumps(impl_result, indent=2)
    body = (
        f"# Milo Engineering Handoff\n\n"
        f"**Capability:** {capability_name}\n"
        f"**Date:** {today_str}\n\n"
        f"---\n\n"
        f"{spec_text}\n\n"
        f"---\n\n"
        f"## Implementation Result\n\n"
        f"```json\n{impl_section}\n```\n"
    )
    try:
        await email_tool.invoke(
            {
                "to": HANDOFF_EMAIL,
                "subject": subject,
                "body": body,
            },
            context,
        )
        logger.info("Handoff email sent for capability '%s'.", capability_name)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send handoff email for '%s': %s", capability_name, exc)
        return False


async def _write_memory_event(
    memory_write_tool: Any,
    context: AgentContext,
    capability_name: str,
    idem_key: str,
    impl_result: dict[str, Any],
) -> None:
    """Record the handoff event in episodic memory."""
    if memory_write_tool is None:
        logger.warning("memory.write tool not available; cannot record memory event.")
        return
    content = (
        f"Hourly monitor filed engineering handoff for capability '{capability_name}'. "
        f"Idempotency key: {idem_key}. "
        f"Timestamp: {datetime.now(timezone.utc).isoformat()}. "
        f"Implementation result status: {impl_result.get('status', 'unknown')}."
    )
    try:
        await memory_write_tool.invoke(
            {
                "kind": "event",
                "content": content,
                "tags": ["hourly_monitor", "handoff", idem_key],
            },
            context,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to write memory event for '%s': %s", capability_name, exc)


# ---------------------------------------------------------------------------
# Core per-tenant logic
# ---------------------------------------------------------------------------

async def _process_tenant(
    db: Session,
    tenant: Tenant,
    milo: Milo,
    run_id: str,
) -> dict[str, Any]:
    """Run the full hourly monitor cycle for a single tenant.

    Returns a summary dict for CloudWatch logging.
    """
    summary: dict[str, Any] = {
        "tenant_id": str(tenant.id),
        "run_id": run_id,
        "gaps_found": 0,
        "handoffs_filed": 0,
        "implement_feature_results": [],
        "emails_sent": 0,
        "skipped": 0,
    }

    # ------------------------------------------------------------------
    # Check if the hourly monitor is enabled for this tenant
    # ------------------------------------------------------------------
    if not getattr(milo, "hourly_monitor_enabled", True):
        logger.info("Hourly monitor disabled for tenant %s – skipping.", tenant.id)
        return summary

    # ------------------------------------------------------------------
    # Bootstrap a throw-away thread + runner
    # ------------------------------------------------------------------
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

    context = AgentContext(
        session=db,
        tenant_id=str(tenant.id),
        milo_id=str(milo.id),
        thread_id=runner.thread_id,
        integration_tokens=runner.integration_tokens,
    )

    # ------------------------------------------------------------------
    # Resolve tools we need directly (avoids building a full agent turn
    # for the audit phase which is deterministic)
    # ------------------------------------------------------------------
    memory_search_tool = registry.get_tool("memory.search")
    memory_write_tool = registry.get_tool("memory.write")
    storage_read_tool = registry.get_tool("storage.read")
    storage_write_tool = registry.get_tool("storage.write")
    work_item_read_tool = registry.get_tool("work_item.read")
    developer_handoff_tool = registry.get_tool("developer.handoff")
    email_send_tool = registry.get_tool("email.send")

    # ------------------------------------------------------------------
    # Step 1 – Read all root work items
    # ------------------------------------------------------------------
    logger.info("[%s] Step 1: reading root work items.", tenant.id)
    if work_item_read_tool is not None:
        try:
            await work_item_read_tool.invoke(
                {"root_only": True, "include_children": True},
                context,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("[%s] work_item.read failed: %s", tenant.id, exc)

    # ------------------------------------------------------------------
    # Step 2 – Audit engineering_requests/ for COMPLETED_ vs pending
    # ------------------------------------------------------------------
    logger.info("[%s] Step 2: auditing engineering_requests/.", tenant.id)
    completed_slugs: set[str] = set()
    if storage_read_tool is not None:
        try:
            result = await storage_read_tool.invoke(
                {"path": "engineering_requests/"},
                context,
            )
            file_list: list[str] = []
            if isinstance(result, dict):
                file_list = result.get("files", result.get("items", []))
            elif isinstance(result, list):
                file_list = result
            for fname in file_list:
                if isinstance(fname, str) and fname.upper().startswith("COMPLETED_"):
                    raw = fname.replace("COMPLETED_", "").replace(".md", "")
                    completed_slugs.add(raw.lower())
        except Exception as exc:  # noqa: BLE001
            logger.warning("[%s] Could not read engineering_requests/: %s", tenant.id, exc)

    # ------------------------------------------------------------------
    # Step 3 – Determine which capabilities are missing / not-yet-live
    # ------------------------------------------------------------------
    logger.info("[%s] Step 3: auditing capability gaps.", tenant.id)
    confirmed_live: set[str] = set(completed_slugs)  # start from storage audit

    if memory_search_tool is not None:
        try:
            mem_result = await memory_search_tool.invoke(
                {"query": "capability confirmed live completed handoff", "top_k": 50},
                context,
            )
            chunks = (
                mem_result.get("chunks", []) if isinstance(mem_result, dict) else []
            )
            for chunk in chunks:
                content = (
                    chunk.get("content", "") if isinstance(chunk, dict) else str(chunk)
                )
                for cap in TARGET_CAPABILITIES:
                    if cap in content and "COMPLETED" in content.upper():
                        confirmed_live.add(cap)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[%s] memory.search for capabilities failed: %s", tenant.id, exc)

    gaps: list[str] = [
        cap for cap in TARGET_CAPABILITIES if cap not in confirmed_live
    ]
    summary["gaps_found"] = len(gaps)
    logger.info("[%s] Capability gaps found: %s", tenant.id, gaps)

    # ------------------------------------------------------------------
    # Step 4 – Process each gap
    # ------------------------------------------------------------------
    for capability_name in gaps:
        slug = _slug(capability_name)
        idem_key = _idempotency_key(slug)

        # 4a – idempotency guard
        already_filed = await _check_idempotency(
            storage_read_tool, memory_search_tool, context, idem_key
        )
        if already_filed:
            summary["skipped"] += 1
            continue

        # 4b – developer.handoff
        spec_text: str = ""
        if developer_handoff_tool is not None:
            try:
                handoff_result = await developer_handoff_tool.invoke(
                    {
                        "title": f"Implement capability: {capability_name}",
                        "description": (
                            f"Milo's hourly program monitor has detected that the "
                            f"'{capability_name}' capability is not yet confirmed live. "
                            f"This handoff requests a full implementation of that capability "
                            f"per the Milo Platform Build Specification."
                        ),
                        "acceptance_criteria": [
                            f"The {capability_name} tool is registered in the tool registry.",
                            f"The tool passes its unit tests with ≥85% line coverage.",
                            f"An integration test exercises a real end-to-end call.",
                            "A COMPLETED_ marker file is created in engineering_requests/.",
                        ],
                        "technical_notes": (
                            f"Capability slug: {slug}. "
                            f"Idempotency key: {idem_key}. "
                            f"Follow the Tool protocol defined in packages/agent/agent/tools/."
                        ),
                    },
                    context,
                )
                if isinstance(handoff_result, dict):
                    spec_text = handoff_result.get("content", handoff_result.get("spec", ""))
                    if not spec_text:
                        spec_text = json.dumps(handoff_result, indent=2)
                else:
                    spec_text = str(handoff_result)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "[%s] developer.handoff failed for '%s': %s", tenant.id, capability_name, exc
                )
                spec_text = (
                    f"# Engineering Handoff: {capability_name}\n\n"
                    f"Capability `{capability_name}` is missing from the live deployment.\n\n"
                    f"Please implement it per the Milo Platform Build Specification, "
                    f"register it in the tool registry, add unit + integration tests, "
                    f"and place a `COMPLETED_{slug}.md` marker in `engineering_requests/`.\n"
                )
        else:
            spec_text = (
                f"# Engineering Handoff: {capability_name}\n\n"
                f"Capability `{capability_name}` is missing from the live deployment.\n\n"
                f"Please implement it per the Milo Platform Build Specification, "
                f"register it in the tool registry, add unit + integration tests, "
                f"and place a `COMPLETED_{slug}.md` marker in `engineering_requests/`.\n"
            )

        summary["handoffs_filed"] += 1

        # 4c – save spec to storage
        await _save_handoff(storage_write_tool, context, slug, spec_text)

        # 4d – call implement_feature (no review gate)
        logger.info("[%s] Calling implement_feature for capability '%s'.", tenant.id, capability_name)
        impl_result = await _invoke_implement_feature(context, spec_text)
        summary["implement_feature_results"].append(
            {"capability": capability_name, "result": impl_result}
        )

        # 4e – send email
        email_sent = await _send_email(
            email_send_tool, context, capability_name, spec_text, impl_result
        )
        if email_sent:
            summary["emails_sent"] += 1

        # 4f – write memory event
        await _write_memory_event(
            memory_write_tool, context, capability_name, idem_key, impl_result
        )

    return summary


# ---------------------------------------------------------------------------
# Lambda entrypoint
# ---------------------------------------------------------------------------

async def _async_handler(event: dict[str, Any], context_obj: Any) -> dict[str, Any]:
    """Async body of the Lambda handler."""
    run_id = str(uuid.uuid4())
    logger.info("Hourly monitor starting. run_id=%s", run_id)

    engine = create_engine(_normalise_db_url(DATABASE_URL))
    all_summaries: list[dict[str, Any]] = []

    try:
        with Session(engine) as db:
            tenants = db.execute(select(Tenant)).scalars().all()
            for tenant in tenants:
                milo = db.execute(
                    select(Milo).where(Milo.tenant_id == tenant.id)
                ).scalar_one_or_none()
                if milo is None:
                    continue
                tenant_summary = await _process_tenant(db, tenant, milo, run_id)
                all_summaries.append(tenant_summary)
    finally:
        engine.dispose()

    total_gaps = sum(s["gaps_found"] for s in all_summaries)
    total_filed = sum(s["handoffs_filed"] for s in all_summaries)
    total_emails = sum(s["emails_sent"] for s in all_summaries)
    total_skipped = sum(s["skipped"] for s in all_summaries)

    log_payload = {
        "run_id": run_id,
        "gaps_found": total_gaps,
        "handoffs_filed": total_filed,
        "implement_feature_results": [
            r for s in all_summaries for r in s["implement_feature_results"]
        ],
        "emails_sent": total_emails,
        "skipped": total_skipped,
        "tenant_summaries": all_summaries,
    }
    logger.info("Hourly monitor complete. %s", json.dumps(log_payload))
    return log_payload


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:  # noqa: ANN401
    """AWS Lambda entrypoint.

    EventBridge Scheduler passes the event as a plain JSON object.
    We run the async body synchronously using asyncio.
    """
    import asyncio  # local import keeps module-level clean for Lambda cold start

    return asyncio.get_event_loop().run_until_complete(_async_handler(event, context))

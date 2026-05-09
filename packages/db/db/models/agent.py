import datetime
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import TenantBoundBase


class Thread(TenantBoundBase):
    __tablename__ = "threads"

    milo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("milos.id", ondelete="CASCADE"))
    work_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("work_items.id", ondelete="SET NULL"), nullable=True
    )
    summary: Mapped[str | None] = mapped_column(String, nullable=True)
    summary_token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Message(TenantBoundBase):
    __tablename__ = "messages"

    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("threads.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String, nullable=False)
    content_jsonb: Mapped[dict] = mapped_column(JSONB, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("role IN ('system', 'user', 'assistant', 'tool')", name="chk_message_role"),
    )


class ToolCall(TenantBoundBase):
    __tablename__ = "tool_calls"

    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"))
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    input_jsonb: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output_jsonb: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime.datetime] = mapped_column(nullable=False)
    finished_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)


class Approval(TenantBoundBase):
    __tablename__ = "approvals"

    milo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("milos.id", ondelete="CASCADE"))
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("threads.id", ondelete="CASCADE"))
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    payload_jsonb: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    expires_at: Mapped[datetime.datetime] = mapped_column(nullable=False)
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'expired')", name="chk_approval_status"
        ),
    )


class AgentRun(TenantBoundBase):
    __tablename__ = "agent_runs"

    milo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("milos.id", ondelete="CASCADE"))
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("threads.id", ondelete="CASCADE"))
    started_at: Mapped[datetime.datetime] = mapped_column(nullable=False)
    finished_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="running")
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'paused', 'done', 'failed')", name="chk_agent_run_status"
        ),
    )


class Notification(TenantBoundBase):
    __tablename__ = "notifications"

    milo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("milos.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    read_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        CheckConstraint("type IN ('approval_required', 'warning', 'info')", name="chk_notification_type"),
    )


class ApprovalRequest(TenantBoundBase):
    __tablename__ = "approval_requests"

    milo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("milos.id", ondelete="CASCADE"))
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("threads.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    options_jsonb: Mapped[dict] = mapped_column(JSONB, nullable=False)
    context_payload_jsonb: Mapped[dict] = mapped_column(JSONB, nullable=False)
    urgency: Mapped[str] = mapped_column(String, nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    response_notes: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    resolved_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'modified', 'expired', 'timeout')", name="chk_approval_req_status"
        ),
        CheckConstraint(
            "urgency IN ('low', 'medium', 'high')", name="chk_approval_req_urgency"
        ),
    )

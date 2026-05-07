import datetime
import uuid

from sqlalchemy import ARRAY, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import TenantBoundBase


class Program(TenantBoundBase):
    __tablename__ = "programs"

    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="initiating")
    charter: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    success_criteria: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('initiating', 'planning', 'executing', 'monitoring', 'closed')",
            name="chk_program_status",
        ),
    )


class Milestone(TenantBoundBase):
    __tablename__ = "milestones"

    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    target_date: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    actual_date: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    dependencies: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(String), nullable=True
    )  # Storing UUIDs as string array or UUID array


class Task(TenantBoundBase):
    __tablename__ = "tasks"

    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"))
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("milestones.id", ondelete="SET NULL"), nullable=True
    )
    assignee_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="todo")
    due_date: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="manual")

    __table_args__ = (CheckConstraint("source IN ('manual', 'agent')", name="chk_task_source"),)


class Stakeholder(TenantBoundBase):
    __tablename__ = "stakeholders"

    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str | None] = mapped_column(String, nullable=True)
    influence: Mapped[str | None] = mapped_column(String, nullable=True)
    interest: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("influence IN ('low', 'med', 'high')", name="chk_sh_influence"),
        CheckConstraint("interest IN ('low', 'med', 'high')", name="chk_sh_interest"),
    )


class Risk(TenantBoundBase):
    __tablename__ = "risks"

    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    likelihood: Mapped[int] = mapped_column(Integer, nullable=False)
    impact: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    mitigation: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("likelihood >= 1 AND likelihood <= 5", name="chk_risk_likelihood"),
        CheckConstraint("impact >= 1 AND impact <= 5", name="chk_risk_impact"),
        CheckConstraint(
            "status IN ('open', 'mitigated', 'realized', 'closed')", name="chk_risk_status"
        ),
    )


class Decision(TenantBoundBase):
    __tablename__ = "decisions"

    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    decision_text: Mapped[str] = mapped_column(Text, nullable=False)
    decided_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    decided_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    alternatives_jsonb: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source_link: Mapped[str | None] = mapped_column(String, nullable=True)


class Commitment(TenantBoundBase):
    __tablename__ = "commitments"

    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"))
    owed_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)  # could be user or stakeholder
    description: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    source_message_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True
    )  # Not a strict FK to avoid circular/cross-schema coupling issues if messages drop

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'met', 'missed')", name="chk_commitment_status"),
    )

import datetime
import uuid

from sqlalchemy import ARRAY, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import TenantBoundBase


import datetime
import uuid

from sqlalchemy import ARRAY, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import TenantBoundBase

class WorkItem(TenantBoundBase):
    __tablename__ = "work_items"

    name: Mapped[str] = mapped_column(String, nullable=False)
    item_type: Mapped[str] = mapped_column(String, nullable=False) # objective, key_result, initiative, project, workstream, milestone, task
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("work_items.id", ondelete="CASCADE"), nullable=True)
    
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_name: Mapped[str | None] = mapped_column(String, nullable=True)
    
    start_date: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    due_date: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    actual_date: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True) # charter, success_criteria, etc
    dependencies: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(String), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "item_type IN ('objective', 'outcome', 'key_result', 'initiative', 'project', 'workstream', 'milestone', 'task')",
            name="chk_work_item_type",
        ),
    )

class Stakeholder(TenantBoundBase):
    __tablename__ = "stakeholders"

    work_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("work_items.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    preferred_communication: Mapped[str | None] = mapped_column(String, default="email", nullable=True)
    role: Mapped[str | None] = mapped_column(String, nullable=True)
    influence: Mapped[str | None] = mapped_column(String, nullable=True)
    interest: Mapped[str | None] = mapped_column(String, nullable=True)
    satisfaction: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("influence IN ('low', 'med', 'high')", name="chk_sh_influence"),
        CheckConstraint("interest IN ('low', 'med', 'high')", name="chk_sh_interest"),
    )


class Risk(TenantBoundBase):
    __tablename__ = "risks"

    work_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("work_items.id", ondelete="CASCADE"))
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

    work_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("work_items.id", ondelete="CASCADE"))
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

    work_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("work_items.id", ondelete="CASCADE"))
    owed_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)  # could be user or stakeholder
    owner_name: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    source_message_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True
    )

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'met', 'missed')", name="chk_commitment_status"),
    )


class ChangeRequest(TenantBoundBase):
    __tablename__ = "change_requests"

    work_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("work_items.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    impact_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'implemented')", name="chk_cr_status"
        ),
    )

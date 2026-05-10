import datetime
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base, TenantBoundBase


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(String, nullable=False, default="solo")
    integration_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now()
    )
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    clerk_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    locale: Mapped[str | None] = mapped_column(String, nullable=True)
    tz: Mapped[str | None] = mapped_column(String, nullable=True)
    preferred_communication: Mapped[str | None] = mapped_column(String, default="email", nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now()
    )


class Membership(Base):
    __tablename__ = "memberships"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("role IN ('owner', 'admin', 'member')", name="chk_membership_role"),
    )


class Milo(TenantBoundBase):
    __tablename__ = "milos"

    name: Mapped[str] = mapped_column(String, nullable=False)
    persona_pack: Mapped[str] = mapped_column(String, nullable=False)
    default_work_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("work_items.id", ondelete="SET NULL"), nullable=True
    )
    autonomy_levels: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    briefing_send_time: Mapped[str] = mapped_column(String, nullable=False, default="07:00", server_default="07:00")
    briefing_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    hourly_monitor_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    __table_args__ = (
        CheckConstraint("persona_pack IN ('trades', 'sme')", name="chk_milo_persona"),
    )

class StakeholderProfile(Base):
    __tablename__ = "stakeholder_profiles"

    sub: Mapped[uuid.UUID] = mapped_column(primary_key=True) # Cognito sub
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    preferred_channel: Mapped[str] = mapped_column(String, default="email", nullable=False)
    frequency: Mapped[str] = mapped_column(String, default="real-time", nullable=False)
    timezone: Mapped[str | None] = mapped_column(String, nullable=True)
    bio: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("preferred_channel IN ('email', 'sms', 'slack', 'teams', 'in-app')", name="chk_sh_pref_channel"),
        CheckConstraint("frequency IN ('real-time', 'daily-digest', 'weekly-summary')", name="chk_sh_freq"),
    )

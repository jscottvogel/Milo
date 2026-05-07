import datetime
import uuid

from sqlalchemy import ARRAY, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import TenantBoundBase


class Integration(TenantBoundBase):
    __tablename__ = "integrations"

    kind: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="connected")
    connected_at: Mapped[datetime.datetime] = mapped_column(nullable=False)
    scopes: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "kind IN ('gmail', 'gcal', 'outlook', 'qbo', 'stripe', 'twilio', 'docusign', 'jobber', 'servicetitan', 'hubspot', 'slack', 'teams')",
            name="chk_integration_kind",
        ),
        CheckConstraint(
            "status IN ('connected', 'degraded', 'disconnected')", name="chk_integration_status"
        ),
    )


class OAuthToken(TenantBoundBase):
    __tablename__ = "oauth_tokens"

    integration_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("integrations.id", ondelete="CASCADE")
    )
    access_token_enc: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    dek_id: Mapped[str | None] = mapped_column(String, nullable=True)


class IntegrationEvent(TenantBoundBase):
    __tablename__ = "integration_events"

    integration_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("integrations.id", ondelete="CASCADE")
    )
    kind: Mapped[str] = mapped_column(String, nullable=False)
    payload_jsonb: Mapped[dict] = mapped_column(JSONB, nullable=False)
    processed_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

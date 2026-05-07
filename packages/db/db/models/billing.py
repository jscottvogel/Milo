import datetime

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import TenantBoundBase


class Subscription(TenantBoundBase):
    __tablename__ = "subscriptions"

    stripe_subscription_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    current_period_end: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    plan_code: Mapped[str] = mapped_column(String, nullable=False)
    trial_ends_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)


class UsageMeter(TenantBoundBase):
    __tablename__ = "usage_meters"

    period_start: Mapped[datetime.datetime] = mapped_column(nullable=False)
    period_end: Mapped[datetime.datetime] = mapped_column(nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0.0)


class InvoicesCache(TenantBoundBase):
    __tablename__ = "invoices_cache"

    stripe_invoice_id: Mapped[str] = mapped_column(String, nullable=False)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    period_start: Mapped[datetime.datetime] = mapped_column(nullable=False)
    period_end: Mapped[datetime.datetime] = mapped_column(nullable=False)

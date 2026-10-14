import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.app.core.database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    username: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )
    role: Mapped[str | None] = mapped_column(Text, default="coach", nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    motto: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_color: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    subscription_tier: Mapped[str | None] = mapped_column(Text, nullable=True)
    override_tier: Mapped[str | None] = mapped_column(Text, nullable=True)
    subscription_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    subscription_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    naf_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    naf_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    naf_stats: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    last_naf_sync: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

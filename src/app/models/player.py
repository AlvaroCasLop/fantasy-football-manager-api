import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[str] = mapped_column(Text, nullable=False)
    spp: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)
    status: Mapped[str | None] = mapped_column(Text, default="active", nullable=True)
    ma: Mapped[int | None] = mapped_column(Integer, nullable=True)
    st: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ag: Mapped[str | None] = mapped_column(Text, nullable=True)
    pa: Mapped[str | None] = mapped_column(Text, nullable=True)
    av: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost: Mapped[int] = mapped_column(Integer, nullable=False)
    ma_mod: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    st_mod: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ag_mod: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pa_mod: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    av_mod: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    niggling: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spp_spent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    advancements: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    tv_added: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fouls_committed: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)
    hired_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )
    pending_advancement: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    is_captain: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    sprint_falls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_veteran: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)

    # Relationships
    team: Mapped["Team | None"] = relationship("Team", back_populates="players")

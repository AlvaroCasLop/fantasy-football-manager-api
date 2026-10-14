import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    league_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leagues.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    race: Mapped[str] = mapped_column(Text, nullable=False)
    treasury: Mapped[int | None] = mapped_column(Integer, default=1000000, nullable=True)
    team_value: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)
    rerolls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assistant_coaches: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cheerleaders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    apothecary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dedicated_fans: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    roster_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    draws: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    group_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    td_for: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    td_against: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cas_for: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cas_against: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fouls_committed: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)
    expensive_mistakes_pending: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    inducements: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    conference_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    allow_free_lineman_skill: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    sprint_falls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dismissed_positionals: Mapped[list[Any] | None] = mapped_column(JSONB, default=list, nullable=True)

    # Relationships
    players: Mapped[list["Player"]] = relationship("Player", back_populates="team", cascade="all, delete-orphan")
    league: Mapped["League | None"] = relationship("League", back_populates="teams")

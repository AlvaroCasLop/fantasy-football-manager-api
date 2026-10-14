import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    creator_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )
    invite_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    format: Mapped[str] = mapped_column(Text, default="standard", nullable=False)
    is_double_round: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    number_of_groups: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_public: Mapped[bool | None] = mapped_column(Boolean, default=True, nullable=True)
    tier_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    star_players_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_star_player_cost: Mapped[int | None] = mapped_column(Integer, nullable=True)
    banned_inducements: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    custom_rules: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft_budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    team_tiers: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    max_primary_skills_per_player: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_secondary_skills_per_player: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_combos_per_player: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_players_with_combo: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(Text, default="draft", nullable=False)
    current_phase: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    mvps_per_match: Mapped[int | None] = mapped_column(Integer, default=1, nullable=True)
    game_mode: Mapped[str | None] = mapped_column(Text, default="standard", nullable=True)
    allow_free_lineman_skill: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    commissioner_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        default=list,
        nullable=False,
    )

    # Relationships
    teams: Mapped[list["Team"]] = relationship("Team", back_populates="league")
    seasons: Mapped[list["Season"]] = relationship("Season", back_populates="league", cascade="all, delete-orphan")
    rounds: Mapped[list["LeagueRound"]] = relationship("LeagueRound", back_populates="league", cascade="all, delete-orphan")
    members: Mapped[list["LeagueMember"]] = relationship("LeagueMember", back_populates="league", cascade="all, delete-orphan")


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    league_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leagues.id", ondelete="CASCADE"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str | None] = mapped_column(Text, default="active", nullable=True)

    league: Mapped["League | None"] = relationship("League", back_populates="seasons")


class LeagueRound(Base):
    __tablename__ = "league_rounds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    league_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leagues.id", ondelete="CASCADE"),
        nullable=False,
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )
    phase: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    extension_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    league: Mapped["League"] = relationship("League", back_populates="rounds")


class LeagueMember(Base):
    __tablename__ = "league_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    league_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leagues.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(Text, default="coach", nullable=False)
    joined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )

    league: Mapped["League"] = relationship("League", back_populates="members")


class LeagueBounty(Base):
    __tablename__ = "league_bounties"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    league_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leagues.id", ondelete="CASCADE"),
        nullable=False,
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
    )
    bounty_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reward_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

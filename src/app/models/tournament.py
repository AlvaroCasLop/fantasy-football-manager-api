import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    format: Mapped[str] = mapped_column(Text, default="single_elimination", nullable=False)
    status: Mapped[str] = mapped_column(Text, default="draft", nullable=False)
    draft_budget: Mapped[int] = mapped_column(Integer, default=1150000, nullable=False)
    max_teams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bonus_t1: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_t2: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_t3: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_t4: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    star_players_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_star_player_cost: Mapped[int | None] = mapped_column(Integer, nullable=True)
    banned_inducements: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    custom_rules: Mapped[str | None] = mapped_column(Text, nullable=True)
    invite_code: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    tier_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    team_tiers: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    max_primary_skills_per_player: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_secondary_skills_per_player: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_combos_per_player: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_players_with_combo: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    winner_team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    game_mode: Mapped[str | None] = mapped_column(Text, default="standard", nullable=True)

    # Relationships
    participants: Mapped[list["TournamentParticipant"]] = relationship(
        "TournamentParticipant",
        back_populates="tournament",
        cascade="all, delete-orphan",
    )
    rounds: Mapped[list["TournamentRound"]] = relationship(
        "TournamentRound",
        back_populates="tournament",
        cascade="all, delete-orphan",
    )
    matches: Mapped[list["TournamentMatch"]] = relationship(
        "TournamentMatch",
        back_populates="tournament",
        cascade="all, delete-orphan",
    )


class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tournament_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tournament: Mapped["Tournament"] = relationship("Tournament", back_populates="participants")


class TournamentRound(Base):
    __tablename__ = "tournament_rounds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tournament_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tournament: Mapped["Tournament"] = relationship("Tournament", back_populates="rounds")
    matches: Mapped[list["TournamentMatch"]] = relationship("TournamentMatch", back_populates="round")


class TournamentMatch(Base):
    __tablename__ = "tournament_matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tournament_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
    )
    round_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tournament_rounds.id", ondelete="CASCADE"),
        nullable=False,
    )
    home_team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    away_team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(Text, default="scheduled", nullable=False)
    played_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    bracket_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    home_cas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_cas: Mapped[int | None] = mapped_column(Integer, nullable=True)

    tournament: Mapped["Tournament"] = relationship("Tournament", back_populates="matches")
    round: Mapped["TournamentRound"] = relationship("TournamentRound", back_populates="matches")

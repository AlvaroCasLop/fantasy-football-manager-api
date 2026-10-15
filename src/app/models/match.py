import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    league_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leagues.id", ondelete="SET NULL"),
        nullable=True,
    )
    home_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    away_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    home_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    away_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    weather: Mapped[str | None] = mapped_column(Text, nullable=True)
    kickoff_event: Mapped[str | None] = mapped_column(Text, nullable=True)
    home_fame: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    away_fame: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    home_winnings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    away_winnings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    played_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(Text, default="scheduled", nullable=False)
    round_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("league_rounds.id", ondelete="SET NULL"),
        nullable=True,
    )
    home_mistake_loss: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    away_mistake_loss: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    home_inducement_treasury: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    away_inducement_treasury: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    home_inducements: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    away_inducements: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    tournament_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tournaments.id", ondelete="SET NULL"),
        nullable=True,
    )
    away_tv: Mapped[int | None] = mapped_column(Integer, nullable=True)
    home_tv: Mapped[int | None] = mapped_column(Integer, nullable=True)
    creator_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    wizard_step: Mapped[int | None] = mapped_column(Integer, default=1, nullable=True)
    wizard_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=dict, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
    home_initial_treasury: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_initial_treasury: Mapped[int | None] = mapped_column(Integer, nullable=True)
    home_no_stall: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    away_no_stall: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)

    # Relationships
    home_team: Mapped["Team"] = relationship("Team", foreign_keys=[home_team_id])
    away_team: Mapped["Team"] = relationship("Team", foreign_keys=[away_team_id])
    round: Mapped["LeagueRound | None"] = relationship(
        "LeagueRound",
        foreign_keys=[round_id],
        back_populates="matches",
    )
    player_events: Mapped[list["MatchPlayerEvent"]] = relationship(
        "MatchPlayerEvent",
        back_populates="match",
        cascade="all, delete-orphan",
    )
    events: Mapped[list["MatchEvent"]] = relationship(
        "MatchEvent",
        back_populates="match",
        cascade="all, delete-orphan",
    )


class MatchPlayerEvent(Base):
    __tablename__ = "match_player_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    touchdowns: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    casualties_caused: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    interceptions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_mvp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    injury_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    fouls_committed: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)
    superb_passes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sprint_falls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    match: Mapped["Match"] = relationship("Match", back_populates="player_events")
    player: Mapped["Player"] = relationship("Player", foreign_keys=[player_id])
    team: Mapped["Team"] = relationship("Team", foreign_keys=[team_id])


class MatchEvent(Base):
    __tablename__ = "match_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
    )
    fouls_committed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    match: Mapped["Match"] = relationship("Match", back_populates="events")

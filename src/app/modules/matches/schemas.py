import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class PlayerEventInput(BaseModel):
    player_id: uuid.UUID
    team_id: uuid.UUID
    touchdowns: int = Field(default=0, ge=0)
    completions: int = Field(default=0, ge=0)
    casualties_caused: int = Field(default=0, ge=0)
    interceptions: int = Field(default=0, ge=0)
    superb_passes: int = Field(default=0, ge=0)
    is_mvp: bool = False
    injury_result: str | None = None  # None | "badly_hurt" | "mng" | "niggling" | "-1_ma" | "-1_av" | "-1_st" | "-1_pa" | "-1_ag" | "dead"
    fouls_committed: int = Field(default=0, ge=0)
    sprint_falls: int = Field(default=0, ge=0)


class PlayerEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    match_id: uuid.UUID
    player_id: uuid.UUID
    team_id: uuid.UUID
    touchdowns: int = 0
    completions: int = 0
    casualties_caused: int = 0
    interceptions: int = 0
    superb_passes: int = 0
    is_mvp: bool = False
    injury_result: str | None = None
    fouls_committed: int = 0
    sprint_falls: int = 0
    spp_earned: int = 0
    player_name: str | None = None
    player_number: int | None = None
    player_position: str | None = None


class MatchBase(BaseModel):
    league_id: uuid.UUID | None = None
    round_id: uuid.UUID | None = None
    tournament_id: uuid.UUID | None = None
    home_team_id: uuid.UUID
    away_team_id: uuid.UUID
    home_score: int = Field(default=0, ge=0)
    away_score: int = Field(default=0, ge=0)
    status: str = "scheduled"  # "scheduled" | "in_progress" | "completed" | "validated"
    weather: str | None = None
    kickoff_event: str | None = None
    home_fame: int = 0
    away_fame: int = 0
    home_winnings: int = 0
    away_winnings: int = 0
    home_tv: int | None = None
    away_tv: int | None = None
    home_inducements: dict[str, Any] = Field(default_factory=dict)
    away_inducements: dict[str, Any] = Field(default_factory=dict)
    played_at: datetime | None = None


class MatchCreate(BaseModel):
    home_team_id: uuid.UUID
    away_team_id: uuid.UUID
    league_id: uuid.UUID | None = None
    round_id: uuid.UUID | None = None
    tournament_id: uuid.UUID | None = None
    played_at: datetime | None = None
    weather: str | None = None
    kickoff_event: str | None = None
    home_tv: int | None = None
    away_tv: int | None = None
    home_inducements: dict[str, Any] = Field(default_factory=dict)
    away_inducements: dict[str, Any] = Field(default_factory=dict)


class MatchUpdate(BaseModel):
    home_score: int | None = Field(default=None, ge=0)
    away_score: int | None = Field(default=None, ge=0)
    status: str | None = None
    weather: str | None = None
    kickoff_event: str | None = None
    home_fame: int | None = None
    away_fame: int | None = None
    home_winnings: int | None = None
    away_winnings: int | None = None
    home_tv: int | None = None
    away_tv: int | None = None
    home_inducements: dict[str, Any] | None = None
    away_inducements: dict[str, Any] | None = None
    wizard_step: int | None = None
    wizard_data: dict[str, Any] | None = None


class MatchResultSubmit(BaseModel):
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)
    weather: str | None = None
    kickoff_event: str | None = None
    home_fame: int = 0
    away_fame: int = 0
    home_winnings: int = 0
    away_winnings: int = 0
    home_mistake_loss: int = 0
    away_mistake_loss: int = 0
    player_events: list[PlayerEventInput] = Field(default_factory=list)


class MatchResponse(MatchBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    home_team_name: str | None = None
    away_team_name: str | None = None
    home_mistake_loss: int = 0
    away_mistake_loss: int = 0
    home_initial_treasury: int | None = None
    away_initial_treasury: int | None = None
    wizard_step: int | None = 1
    updated_at: datetime | None = None


class MatchDetailResponse(MatchResponse):
    player_events: list[PlayerEventResponse] = Field(default_factory=list)
    wizard_data: dict[str, Any] | None = Field(default_factory=dict)

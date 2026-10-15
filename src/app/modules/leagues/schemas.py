import uuid
from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from src.app.modules.matches.schemas import MatchResponse
from src.app.modules.teams.schemas import TeamResponse


class LeagueBase(BaseModel):
    name: str
    description: str | None = None
    format: str = "standard"  # "standard" | "round_robin" | "swiss" | "playoff" | "custom"
    game_mode: str = "standard"  # "standard" | "sevens" | "dungeonbowl" | "gnoblar"
    is_double_round: bool = False
    number_of_groups: int | None = None
    is_public: bool = True
    logo_url: str | None = None
    custom_rules: str | None = None
    star_players_banned: bool = False
    max_star_player_cost: int | None = None
    banned_inducements: list[Any] = Field(default_factory=list)
    draft_budget: int | None = None
    team_tiers: dict[str, Any] = Field(default_factory=dict)
    tier_rules: dict[str, Any] = Field(default_factory=dict)
    max_primary_skills_per_player: int = 1
    max_secondary_skills_per_player: int = 1
    max_combos_per_player: int = 0
    max_players_with_combo: int = 0
    mvps_per_match: int = 1
    allow_free_lineman_skill: bool = False


class LeagueCreate(LeagueBase):
    invite_code: str | None = None
    creator_id: uuid.UUID | None = None


class LeagueUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    format: str | None = None
    game_mode: str | None = None
    is_double_round: bool | None = None
    number_of_groups: int | None = None
    is_public: bool | None = None
    logo_url: str | None = None
    custom_rules: str | None = None
    star_players_banned: bool | None = None
    max_star_player_cost: int | None = None
    banned_inducements: list[Any] | None = None
    draft_budget: int | None = None
    team_tiers: dict[str, Any] | None = None
    tier_rules: dict[str, Any] | None = None
    max_primary_skills_per_player: int | None = None
    max_secondary_skills_per_player: int | None = None
    max_combos_per_player: int | None = None
    max_players_with_combo: int | None = None
    status: str | None = None  # "draft" | "active" | "completed" | "archived"
    current_phase: int | None = None
    mvps_per_match: int | None = None
    allow_free_lineman_skill: bool | None = None
    commissioner_ids: list[uuid.UUID] | None = None


class LeagueResponse(LeagueBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    creator_id: uuid.UUID | None = None
    invite_code: str
    status: str = "draft"
    current_phase: int = 1
    created_at: datetime | None = None
    commissioner_ids: list[uuid.UUID] = Field(default_factory=list)
    teams_count: int = 0


class LeagueDetailResponse(LeagueResponse):
    teams: list[TeamResponse] = Field(default_factory=list)


class LeagueMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    league_id: uuid.UUID
    user_id: uuid.UUID
    role: str = "coach"
    joined_at: datetime | None = None


class JoinLeagueRequest(BaseModel):
    invite_code: str
    team_id: uuid.UUID | None = None


# ==============================================================================
# LEAGUE ROUNDS & SCHEDULE SCHEMAS
# ==============================================================================


class LeagueRoundBase(BaseModel):
    round_number: int
    name: str
    phase: int = 1
    start_date: date | None = None
    end_date: date | None = None
    extension_days: int = 0


class LeagueRoundCreate(LeagueRoundBase):
    pass


class LeagueRoundUpdate(BaseModel):
    name: str | None = None
    round_number: int | None = None
    phase: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    extension_days: int | None = None


class LeagueRoundResponse(LeagueRoundBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    league_id: uuid.UUID
    created_at: datetime | None = None


class LeagueRoundDetailResponse(LeagueRoundResponse):
    matches: list[MatchResponse] = Field(default_factory=list)
    matches_count: int = 0
    completed_matches_count: int = 0


# ==============================================================================
# SCHEDULE GENERATION SCHEMAS
# ==============================================================================


class CustomMatchInput(BaseModel):
    home_team_id: uuid.UUID
    away_team_id: uuid.UUID


class CustomRoundInput(BaseModel):
    number: int | None = None
    name: str | None = None
    phase: int = 1
    start_date: date | None = None
    end_date: date | None = None
    matches: list[CustomMatchInput] = Field(default_factory=list)


class ScheduleGenerateRequest(BaseModel):
    format: str = "round_robin"  # "round_robin" | "groups_playoffs" | "conferences_groups" | "custom_manual"
    is_double_round: bool = False
    number_of_groups: int = 2
    assignment_mode: str = "random"  # "random" | "manual"
    team_assignments: dict[str, dict[str, str]] | None = None  # team_id -> {"group": "A", "conf": "Este"}
    start_date: date | None = None
    round_interval_days: int = 7
    replace_existing: bool = False
    custom_rounds: list[CustomRoundInput] | None = None


class ScheduleGenerateResponse(BaseModel):
    league_id: uuid.UUID
    format: str
    rounds_created: int
    matches_created: int
    rounds: list[LeagueRoundDetailResponse] = Field(default_factory=list)


# ==============================================================================
# PLAYOFF GENERATION SCHEMAS
# ==============================================================================


class PlayoffGenerateRequest(BaseModel):
    format: str = "semis"  # "final_directa" | "semis" | "cuartos" | "doble_elim"
    round_number: int | None = None
    name: str | None = None
    phase: int = 2
    qualified_team_ids: list[uuid.UUID] | None = None
    start_date: date | None = None
    end_date: date | None = None


class PlayoffGenerateResponse(BaseModel):
    league_id: uuid.UUID
    format: str
    round: LeagueRoundDetailResponse

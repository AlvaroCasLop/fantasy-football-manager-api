import uuid
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from src.app.modules.players.schemas import PlayerResponse


class TeamBase(BaseModel):
    name: str
    race: str
    group_name: str | None = None
    conference_name: str | None = None
    logo_url: str | None = None


class TeamCreate(TeamBase):
    league_id: uuid.UUID | None = None
    treasury: int = 1000000
    rerolls: int = 0
    assistant_coaches: int = 0
    cheerleaders: int = 0
    apothecary: bool = False
    dedicated_fans: int = 1


class TeamUpdate(BaseModel):
    name: str | None = None
    treasury: int | None = None
    rerolls: int | None = None
    assistant_coaches: int | None = None
    cheerleaders: int | None = None
    apothecary: bool | None = None
    dedicated_fans: int | None = None
    roster_closed: bool | None = None
    group_name: str | None = None
    conference_name: str | None = None
    logo_url: str | None = None
    allow_free_lineman_skill: bool | None = None


class TeamResponse(TeamBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID | None = None
    league_id: uuid.UUID | None = None
    treasury: int = 1000000
    team_value: int = 0
    rerolls: int = 0
    assistant_coaches: int = 0
    cheerleaders: int = 0
    apothecary: bool = False
    dedicated_fans: int = 1
    roster_closed: bool = False
    wins: int = 0
    draws: int = 0
    losses: int = 0
    played: int = 0
    td_for: int = 0
    td_against: int = 0
    cas_for: int = 0
    cas_against: int = 0
    fouls_committed: int = 0
    expensive_mistakes_pending: bool = False
    inducements: dict[str, Any] = Field(default_factory=dict)
    allow_free_lineman_skill: bool = False
    sprint_falls: int = 0
    dismissed_positionals: list[Any] = Field(default_factory=list)


class TeamDetailResponse(TeamResponse):
    players: list[PlayerResponse] = Field(default_factory=list)

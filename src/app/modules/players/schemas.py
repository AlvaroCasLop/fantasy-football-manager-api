import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class PlayerBase(BaseModel):
    name: str
    number: int
    position: str
    cost: int
    ma: int | None = None
    st: int | None = None
    ag: str | None = None
    pa: str | None = None
    av: str | None = None


class PlayerCreate(PlayerBase):
    team_id: uuid.UUID
    status: str = "active"
    is_captain: bool = False
    is_veteran: bool = False


class PlayerUpdate(BaseModel):
    name: str | None = None
    number: int | None = None
    position: str | None = None
    status: str | None = None
    spp: int | None = None
    spp_spent: int | None = None
    tv_added: int | None = None
    advancements: list[Any] | None = None
    niggling: int | None = None
    fouls_committed: int | None = None
    sprint_falls: int | None = None
    is_captain: bool | None = None
    is_veteran: bool | None = None



class PlayerAdvancement(BaseModel):
    type: str = "primary"  # "primary" | "secondary" | "random_primary" | "random_secondary" | "stat"
    skill: str | None = None
    stat: str | None = None
    tv_cost: int | None = Field(
        default=None,
        description="Optional override for TV cost. If omitted, calculated automatically based on skill/tier/elite.",
    )
    spp_cost: int | None = Field(
        default=None,
        description="Optional override for SPP cost. If omitted, calculated automatically based on official SPP progression table.",
    )



class PlayerResponse(PlayerBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    team_id: uuid.UUID | None = None
    spp: int = 0
    status: str = "active"
    ma_mod: int = 0
    st_mod: int = 0
    ag_mod: int = 0
    pa_mod: int = 0
    av_mod: int = 0
    niggling: int = 0
    spp_spent: int = 0
    advancements: list[Any] = Field(default_factory=list)
    tv_added: int = 0
    fouls_committed: int = 0
    hired_at: datetime | None = None
    pending_advancement: dict[str, Any] | None = None
    is_captain: bool = False
    sprint_falls: int = 0
    is_veteran: bool = False

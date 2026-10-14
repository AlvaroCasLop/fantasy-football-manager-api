import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.core.security import UserTokenPayload, get_current_user, get_optional_user
from src.app.modules.teams.schemas import (
    TeamCreate,
    TeamDetailResponse,
    TeamResponse,
    TeamUpdate,
)
from src.app.modules.teams.service import team_service

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("", response_model=list[TeamResponse])
async def list_teams(
    league_id: uuid.UUID | None = Query(None, description="Filter by league ID"),
    owner_id: uuid.UUID | None = Query(None, description="Filter by owner ID"),
    db: AsyncSession = Depends(get_db),
) -> list[TeamResponse]:
    """List all teams, optionally filtered by league or owner."""
    return await team_service.list_teams(db, league_id=league_id, owner_id=owner_id)


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_in: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTokenPayload | None = Depends(get_optional_user),
) -> TeamResponse:
    """Create a new team.

    Associates with authenticated user if token is provided.
    """
    owner_uuid = uuid.UUID(current_user.id) if current_user and current_user.id != "dev-user-id" else None
    return await team_service.create_team(db, team_in, owner_id=owner_uuid)


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TeamDetailResponse:
    """Get full team details, including current roster and staff."""
    team = await team_service.get_team(db, team_id, load_players=True)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with id '{team_id}' not found",
        )
    return team


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: uuid.UUID,
    team_in: TeamUpdate,
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    """Update team staff, settings, or details."""
    team = await team_service.get_team(db, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with id '{team_id}' not found",
        )
    return await team_service.update_team(db, team, team_in)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a team and its roster."""
    team = await team_service.get_team(db, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with id '{team_id}' not found",
        )
    await team_service.delete_team(db, team)

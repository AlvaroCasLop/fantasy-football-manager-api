import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.core.security import UserTokenPayload, get_optional_user
from src.app.modules.leagues.schemas import (
    JoinLeagueRequest,
    LeagueCreate,
    LeagueDetailResponse,
    LeagueResponse,
    LeagueUpdate,
)
from src.app.modules.leagues.service import league_service

router = APIRouter(prefix="/leagues", tags=["Leagues"])


@router.get("", response_model=list[LeagueResponse])
async def list_leagues(
    is_public: bool | None = Query(None, description="Filter by public visibility"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status (draft, active, completed)"),
    creator_id: uuid.UUID | None = Query(None, description="Filter by commissioner/creator ID"),
    db: AsyncSession = Depends(get_db),
) -> list[LeagueResponse]:
    """List all leagues with optional public, status, or creator filters."""
    return await league_service.list_leagues(
        db,
        is_public=is_public,
        status=status_filter,
        creator_id=creator_id,
    )


@router.post("", response_model=LeagueResponse, status_code=status.HTTP_201_CREATED)
async def create_league(
    league_in: LeagueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTokenPayload | None = Depends(get_optional_user),
) -> LeagueResponse:
    """Create a new competition league with custom rules and an auto-generated invite code."""
    creator_uuid: uuid.UUID | None = None
    if current_user and current_user.id != "dev-user-id":
        try:
            creator_uuid = uuid.UUID(current_user.id)
        except ValueError:
            pass

    return await league_service.create_league(db, league_in, creator_id=creator_uuid)


@router.get("/code/{invite_code}", response_model=LeagueDetailResponse)
async def get_league_by_code(
    invite_code: str,
    db: AsyncSession = Depends(get_db),
) -> LeagueDetailResponse:
    """Look up a league by its unique invite code (e.g. for joining)."""
    league = await league_service.get_league_by_invite_code(db, invite_code, load_teams=True)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"League with invite code '{invite_code}' not found",
        )
    return league


@router.get("/{league_id}", response_model=LeagueDetailResponse)
async def get_league(
    league_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> LeagueDetailResponse:
    """Get full league details, configuration, rules, and enrolled teams."""
    league = await league_service.get_league(db, league_id, load_teams=True)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"League with id '{league_id}' not found",
        )
    return league


@router.patch("/{league_id}", response_model=LeagueResponse)
async def update_league(
    league_id: uuid.UUID,
    league_in: LeagueUpdate,
    db: AsyncSession = Depends(get_db),
) -> LeagueResponse:
    """Update league rules, format, phase, or status."""
    league = await league_service.get_league(db, league_id)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"League with id '{league_id}' not found",
        )
    return await league_service.update_league(db, league, league_in)


@router.delete("/{league_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_league(
    league_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a league."""
    league = await league_service.get_league(db, league_id)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"League with id '{league_id}' not found",
        )
    await league_service.delete_league(db, league)


@router.post("/join", response_model=LeagueDetailResponse)
@router.post("/{league_id}/join", response_model=LeagueDetailResponse)
async def join_league(
    join_in: JoinLeagueRequest,
    league_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserTokenPayload | None = Depends(get_optional_user),
) -> LeagueDetailResponse:
    """Join a league using its invite code and optionally enroll a team."""
    league: Any = None
    if league_id:
        league = await league_service.get_league(db, league_id)
    if not league:
        league = await league_service.get_league_by_invite_code(db, join_in.invite_code)

    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found with the provided id or invite code",
        )

    # Determine user id
    user_uuid = uuid.uuid4()
    if current_user and current_user.id != "dev-user-id":
        try:
            user_uuid = uuid.UUID(current_user.id)
        except ValueError:
            pass

    return await league_service.join_league(db, league, user_id=user_uuid, team_id=join_in.team_id)

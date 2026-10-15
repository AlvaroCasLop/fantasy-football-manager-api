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
    LeagueRoundDetailResponse,
    LeagueRoundUpdate,
    LeagueUpdate,
    PlayoffGenerateRequest,
    PlayoffGenerateResponse,
    ScheduleGenerateRequest,
    ScheduleGenerateResponse,
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
        league = await league_service.get_league(db, league_id, load_teams=True)
    if not league:
        league = await league_service.get_league_by_invite_code(db, join_in.invite_code, load_teams=True)

    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found with the provided id or invite code",
        )

    # Determine user id if authenticated
    user_uuid: uuid.UUID | None = None
    if current_user and current_user.id != "dev-user-id":
        try:
            user_uuid = uuid.UUID(current_user.id)
        except ValueError:
            pass

    return await league_service.join_league(db, league, user_id=user_uuid, team_id=join_in.team_id)


# ==============================================================================
# SCHEDULE & ROUND MANAGEMENT ENDPOINTS
# ==============================================================================


@router.post(
    "/{league_id}/generate-schedule",
    response_model=ScheduleGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_schedule(
    league_id: uuid.UUID,
    schedule_in: ScheduleGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> ScheduleGenerateResponse:
    """Generate round-robin, groups, or manual match schedule for a league."""
    league = await league_service.get_league(db, league_id)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"League with id '{league_id}' not found",
        )
    return await league_service.generate_schedule(db, league, schedule_in)


@router.get(
    "/{league_id}/rounds",
    response_model=list[LeagueRoundDetailResponse],
)
async def list_league_rounds(
    league_id: uuid.UUID,
    phase: int | None = Query(None, description="Filter rounds by phase (e.g. 1 for regular season, 2 for playoffs)"),
    db: AsyncSession = Depends(get_db),
) -> list[LeagueRoundDetailResponse]:
    """List all rounds for a league with their scheduled matches and statuses."""
    league = await league_service.get_league(db, league_id)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"League with id '{league_id}' not found",
        )
    return await league_service.list_rounds(db, league_id, phase=phase)


@router.patch(
    "/rounds/{round_id}",
    response_model=LeagueRoundDetailResponse,
)
async def update_league_round(
    round_id: uuid.UUID,
    round_in: LeagueRoundUpdate,
    db: AsyncSession = Depends(get_db),
) -> LeagueRoundDetailResponse:
    """Update round metadata: dates (start_date, end_date), extension_days, phase, or name."""
    round_obj = await league_service.get_round(db, round_id)
    if not round_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"League round with id '{round_id}' not found",
        )
    return await league_service.update_round(db, round_obj, round_in)


@router.delete(
    "/rounds/{round_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_league_round(
    round_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a round and its scheduled matches if none are completed."""
    round_obj = await league_service.get_round(db, round_id)
    if not round_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"League round with id '{round_id}' not found",
        )
    await league_service.delete_round(db, round_obj)


@router.post(
    "/{league_id}/playoffs",
    response_model=PlayoffGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_playoffs(
    league_id: uuid.UUID,
    playoff_in: PlayoffGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> PlayoffGenerateResponse:
    """Generate playoff bracket (final_directa, semis, cuartos, doble_elim) based on league standings."""
    league = await league_service.get_league(db, league_id)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"League with id '{league_id}' not found",
        )
    return await league_service.generate_playoffs(db, league, playoff_in)


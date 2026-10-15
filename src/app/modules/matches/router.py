import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.core.security import UserTokenPayload, get_optional_user
from src.app.modules.matches.schemas import (
    MatchCreate,
    MatchDetailResponse,
    MatchResponse,
    MatchResultSubmit,
    MatchUpdate,
)
from src.app.modules.matches.service import match_service

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("", response_model=list[MatchResponse])
async def list_matches(
    league_id: uuid.UUID | None = Query(None, description="Filter by league ID"),
    round_id: uuid.UUID | None = Query(None, description="Filter by league round ID"),
    team_id: uuid.UUID | None = Query(None, description="Filter by participating team ID (home or away)"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status (scheduled, in_progress, completed, validated)"),
    db: AsyncSession = Depends(get_db),
) -> list[MatchResponse]:
    """List matches with optional filters by league, round, team, or status."""
    return await match_service.list_matches(
        db,
        league_id=league_id,
        round_id=round_id,
        team_id=team_id,
        status=status_filter,
    )


@router.post("", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match(
    match_in: MatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTokenPayload | None = Depends(get_optional_user),
) -> MatchResponse:
    """Schedule a new match between two teams."""
    creator_uuid: uuid.UUID | None = None
    if current_user and current_user.id != "dev-user-id":
        try:
            creator_uuid = uuid.UUID(current_user.id)
        except ValueError:
            pass

    return await match_service.create_match(db, match_in, creator_id=creator_uuid)


@router.get("/{match_id}", response_model=MatchDetailResponse)
async def get_match(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MatchDetailResponse:
    """Get match details, including scores, weather, and player events."""
    match = await match_service.get_match(db, match_id, load_details=True)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id '{match_id}' not found",
        )
    return match_service._to_match_detail_response(match)


@router.patch("/{match_id}", response_model=MatchResponse)
async def update_match(
    match_id: uuid.UUID,
    match_in: MatchUpdate,
    db: AsyncSession = Depends(get_db),
) -> MatchResponse:
    """Update match in-progress state, pre-match inducements, or status."""
    match = await match_service.get_match(db, match_id)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id '{match_id}' not found",
        )
    return await match_service.update_match(db, match, match_in)


@router.post("/{match_id}/result", response_model=MatchDetailResponse)
async def record_match_result(
    match_id: uuid.UUID,
    result_in: MatchResultSubmit,
    db: AsyncSession = Depends(get_db),
) -> MatchDetailResponse:
    """Submit the official post-match sheet: records scores, awards SPP to players,
    applies injuries, and updates team standings and treasuries.
    """
    match = await match_service.get_match(db, match_id, load_details=True)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id '{match_id}' not found",
        )
    return await match_service.record_match_result(db, match, result_in)


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_match(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a match."""
    match = await match_service.get_match(db, match_id)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id '{match_id}' not found",
        )
    await match_service.delete_match(db, match)

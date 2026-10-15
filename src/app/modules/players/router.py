import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.modules.players.schemas import (
    PlayerAdvancement,
    PlayerCreate,
    PlayerResponse,
    PlayerUpdate,
)
from src.app.modules.players.service import player_service
from src.app.modules.teams.service import team_service

router = APIRouter(tags=["Players"])


@router.get("/teams/{team_id}/players", response_model=list[PlayerResponse])
async def list_team_players(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[PlayerResponse]:
    """List all players on a specific team roster."""
    team = await team_service.get_team(db, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with id '{team_id}' not found",
        )
    return await player_service.list_players_by_team(db, team_id)


@router.post("/teams/{team_id}/players", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
async def hire_player(
    team_id: uuid.UUID,
    player_in: PlayerCreate,
    db: AsyncSession = Depends(get_db),
) -> PlayerResponse:
    """Hire a new player to the team roster and update treasury and TV."""
    team = await team_service.get_team(db, team_id, load_players=True)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with id '{team_id}' not found",
        )

    # Validate roster limit (Max 16 players)
    if len(team.players) >= 16:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot hire player: Team already has maximum 16 players",
        )

    # Validate treasury
    if team.treasury is not None and team.treasury < player_in.cost:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot hire player: Insufficient treasury ({team.treasury} < {player_in.cost})",
        )

    player_in.team_id = team_id
    return await player_service.create_player(db, player_in)


@router.get("/players/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PlayerResponse:
    """Get player details, stats, and advancements."""
    player = await player_service.get_player(db, player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found",
        )
    return player


@router.patch("/players/{player_id}", response_model=PlayerResponse)
async def update_player(
    player_id: uuid.UUID,
    player_in: PlayerUpdate,
    db: AsyncSession = Depends(get_db),
) -> PlayerResponse:
    """Update player details (number, status, captain status, etc.)."""
    player = await player_service.get_player(db, player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found",
        )
    return await player_service.update_player(db, player, player_in)


@router.get("/players/{player_id}/advancements", response_model=list[dict[str, Any]])
@router.get("/players/{player_id}/advancements/", response_model=list[dict[str, Any]], include_in_schema=False)
async def list_player_advancements(
    player_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List all recorded advancements for a specific player."""
    player = await player_service.get_player(db, player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found",
        )
    return list(player.advancements or [])


@router.patch("/players/{player_id}/advancements", response_model=PlayerResponse)
@router.post("/players/{player_id}/advancements", response_model=PlayerResponse)
@router.patch("/players/{player_id}/advancements/", response_model=PlayerResponse, include_in_schema=False)
@router.post("/players/{player_id}/advancements/", response_model=PlayerResponse, include_in_schema=False)
async def add_advancement(
    player_id: uuid.UUID,
    adv: PlayerAdvancement,
    db: AsyncSession = Depends(get_db),
) -> PlayerResponse:
    """Spend SPP to grant a player a skill or characteristic increase."""

    player = await player_service.get_player(db, player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found",
        )

    # Calculate effective costs dynamically (respecting optional overrides)
    effective_tv_cost, effective_spp_cost = player_service.calculate_advancement_costs(player, adv)

    available_spp = (player.spp or 0) - (player.spp_spent or 0)
    if available_spp < effective_spp_cost:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Insufficient SPP available: {available_spp} available, requires {effective_spp_cost}",
        )

    return await player_service.add_advancement(
        db,
        player,
        adv,
        effective_tv_cost=effective_tv_cost,
        effective_spp_cost=effective_spp_cost,
    )



@router.delete("/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_player(
    player_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Dismiss a player from the team."""
    player = await player_service.get_player(db, player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found",
        )
    await player_service.delete_player(db, player)

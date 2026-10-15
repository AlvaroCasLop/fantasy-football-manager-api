from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from src.app.modules.reference_data.service import reference_data_service

router = APIRouter(prefix="/reference", tags=["Reference Data"])


@router.get("/skills", response_model=dict[str, Any])
async def get_skills(
    category: str | None = Query(None, description="Filter by category code, e.g. G, A, P, S, M, D, T"),
    elite_only: bool = Query(False, description="Filter only elite skills"),
) -> dict[str, Any]:
    """Retrieve the skills catalog, categories, and glossary."""
    data = reference_data_service.get_skills_data()
    glossary = list(data.get("glossary", []))

    if category:
        cat_upper = category.strip().upper()
        glossary = [s for s in glossary if s.get("category") == cat_upper]

    if elite_only:
        glossary = [s for s in glossary if s.get("is_elite") is True]

    return {
        "categories": data.get("categories", {}),
        "elite_skills": data.get("elite_skills", []),
        "category_map": data.get("category_map", {}),
        "skills": glossary,
    }


@router.get("/skills/elite", response_model=list[dict[str, Any]])
async def get_elite_skills() -> list[dict[str, Any]]:
    """Retrieve all skills marked as Elite."""
    elite_ids = reference_data_service.get_elite_skills()
    return reference_data_service.resolve_skills(elite_ids)


@router.get("/skills/{skill_id_or_name}", response_model=dict[str, Any])
async def get_skill(skill_id_or_name: str) -> dict[str, Any]:
    """Retrieve details of a specific skill by canonical ID or name."""
    skill = reference_data_service.get_skill(skill_id_or_name)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id_or_name}' not found",
        )
    return skill


@router.get("/races", response_model=dict[str, Any])
async def get_races() -> dict[str, Any]:
    """Retrieve all official races and their positional rosters with canonical skill IDs."""
    return reference_data_service.get_races()


@router.get("/races/{race_name}", response_model=dict[str, Any])
async def get_race(race_name: str) -> dict[str, Any]:
    """Retrieve details and positionals for a specific race."""
    race = reference_data_service.get_race(race_name)
    if not race:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Race '{race_name}' not found",
        )
    return race


@router.get("/stars", response_model=list[dict[str, Any]])
async def get_stars() -> list[dict[str, Any]]:
    """Retrieve all Star Players with their stats, cost, and canonical skill IDs."""
    return reference_data_service.get_stars()


@router.get("/stars/{star_id_or_name}", response_model=dict[str, Any])
async def get_star(star_id_or_name: str) -> dict[str, Any]:
    """Retrieve a specific Star Player by id or name."""
    star = reference_data_service.get_star(star_id_or_name)
    if not star:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Star player '{star_id_or_name}' not found",
        )
    return star


@router.get("/inducements", response_model=list[dict[str, Any]])
async def get_inducements() -> list[dict[str, Any]]:
    """Retrieve all standard inducements."""
    return reference_data_service.get_inducements()

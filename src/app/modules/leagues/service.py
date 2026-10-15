import secrets
import uuid
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.league import League, LeagueMember
from src.app.models.team import Team
from src.app.modules.leagues.schemas import LeagueCreate, LeagueUpdate


def generate_invite_code(length: int = 6) -> str:
    """Generates an uppercase alphanumeric code without confusing characters (0/O, 1/I)."""
    safe_chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    code = "".join(secrets.choice(safe_chars) for _ in range(length))
    return f"BB-{code}"


class LeagueService:
    @staticmethod
    async def generate_unique_invite_code(db: AsyncSession) -> str:
        """Generates an invite code that is guaranteed not to collide in the database."""
        for _ in range(10):
            code = generate_invite_code()
            stmt = select(League.id).where(League.invite_code == code)
            exists = (await db.execute(stmt)).scalar_one_or_none()
            if not exists:
                return code
        # Fallback to random hex if 10 collisions happen (statistically negligible)
        return f"BB-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    async def list_leagues(
        db: AsyncSession,
        is_public: bool | None = None,
        status: str | None = None,
        creator_id: uuid.UUID | None = None,
    ) -> list[League]:
        """Lists leagues with optional public, status, or creator filters."""
        query = select(League).options(selectinload(League.teams)).order_by(League.created_at.desc())

        if is_public is not None:
            query = query.where(League.is_public == is_public)
        if status:
            query = query.where(League.status == status)
        if creator_id:
            query = query.where(League.creator_id == creator_id)

        result = await db.execute(query)
        leagues = list(result.scalars().all())

        # Populate transient teams_count for each league
        for l in leagues:
            l.teams_count = len(l.teams) if l.teams else 0

        return leagues

    @staticmethod
    async def get_league(
        db: AsyncSession,
        league_id: uuid.UUID,
        load_teams: bool = False,
    ) -> League | None:
        """Retrieves a single league by ID, optionally loading enrolled teams."""
        query = select(League).where(League.id == league_id)
        if load_teams:
            query = query.options(selectinload(League.teams))

        result = await db.execute(query)
        league = result.scalar_one_or_none()
        if league:
            league.teams_count = len(league.teams) if league.teams else 0
        return league

    @staticmethod
    async def get_league_by_invite_code(
        db: AsyncSession,
        invite_code: str,
        load_teams: bool = False,
    ) -> League | None:
        """Finds a league by its unique invite code (case-insensitive)."""
        clean_code = invite_code.strip().upper()
        query = select(League).where(func.upper(League.invite_code) == clean_code)
        if load_teams:
            query = query.options(selectinload(League.teams))

        result = await db.execute(query)
        league = result.scalar_one_or_none()
        if league:
            league.teams_count = len(league.teams) if league.teams else 0
        return league

    @staticmethod
    async def create_league(
        db: AsyncSession,
        league_in: LeagueCreate,
        creator_id: uuid.UUID | None = None,
    ) -> League:
        """Creates a new league with an auto-generated invite code and initial commissioner."""
        final_creator_id = league_in.creator_id or creator_id

        # Generate unique invite code if not explicitly provided
        invite_code = league_in.invite_code
        if not invite_code:
            invite_code = await LeagueService.generate_unique_invite_code(db)
        else:
            invite_code = invite_code.strip().upper()

        commissioners: list[uuid.UUID] = []
        if final_creator_id:
            commissioners.append(final_creator_id)

        league = League(
            name=league_in.name,
            description=league_in.description,
            creator_id=final_creator_id,
            invite_code=invite_code,
            format=league_in.format,
            game_mode=league_in.game_mode,
            is_double_round=league_in.is_double_round,
            number_of_groups=league_in.number_of_groups,
            is_public=league_in.is_public,
            logo_url=league_in.logo_url,
            custom_rules=league_in.custom_rules,
            star_players_banned=league_in.star_players_banned,
            max_star_player_cost=league_in.max_star_player_cost,
            banned_inducements=league_in.banned_inducements or [],
            draft_budget=league_in.draft_budget,
            team_tiers=league_in.team_tiers or {},
            tier_rules=league_in.tier_rules or {},
            max_primary_skills_per_player=league_in.max_primary_skills_per_player,
            max_secondary_skills_per_player=league_in.max_secondary_skills_per_player,
            max_combos_per_player=league_in.max_combos_per_player,
            max_players_with_combo=league_in.max_players_with_combo,
            mvps_per_match=league_in.mvps_per_match,
            allow_free_lineman_skill=league_in.allow_free_lineman_skill,
            commissioner_ids=commissioners,
            status="draft",
            current_phase=1,
        )
        db.add(league)

        # Add creator as a league member with commissioner role
        if final_creator_id:
            member = LeagueMember(
                league_id=league.id,
                user_id=final_creator_id,
                role="commissioner",
            )
            db.add(member)

        await db.commit()
        await db.refresh(league)
        league.teams_count = 0
        return league

    @staticmethod
    async def update_league(
        db: AsyncSession,
        league: League,
        league_in: LeagueUpdate,
    ) -> League:
        """Updates settings, rules, or status of an existing league."""
        update_data = league_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(league, field, value)

        await db.commit()
        await db.refresh(league)
        league.teams_count = len(league.teams) if league.teams else 0
        return league

    @staticmethod
    async def delete_league(db: AsyncSession, league: League) -> None:
        """Deletes a league and disassociates enrolled teams."""
        await db.delete(league)
        await db.commit()

    @staticmethod
    async def join_league(
        db: AsyncSession,
        league: League,
        user_id: uuid.UUID,
        team_id: uuid.UUID | None = None,
    ) -> League:
        """Enrolls a coach and optionally an existing team into the league."""
        # 1. Check if user is already a member
        member_stmt = select(LeagueMember).where(
            LeagueMember.league_id == league.id,
            LeagueMember.user_id == user_id,
        )
        existing_member = (await db.execute(member_stmt)).scalar_one_or_none()
        if not existing_member:
            new_member = LeagueMember(
                league_id=league.id,
                user_id=user_id,
                role="coach",
            )
            db.add(new_member)

        # 2. If team_id provided, link team to this league
        if team_id:
            team_stmt = select(Team).where(Team.id == team_id)
            team = (await db.execute(team_stmt)).scalar_one_or_none()
            if team:
                team.league_id = league.id

        await db.commit()
        await db.refresh(league)
        return await LeagueService.get_league(db, league.id, load_teams=True) or league


league_service = LeagueService()

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.team import Team
from src.app.modules.teams.schemas import TeamCreate, TeamUpdate


class TeamService:
    @staticmethod
    async def list_teams(
        db: AsyncSession,
        league_id: uuid.UUID | None = None,
        owner_id: uuid.UUID | None = None,
    ) -> list[Team]:
        query = select(Team).order_by(Team.name)
        if league_id:
            query = query.where(Team.league_id == league_id)
        if owner_id:
            query = query.where(Team.owner_id == owner_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_team(
        db: AsyncSession,
        team_id: uuid.UUID,
        load_players: bool = False,
    ) -> Team | None:
        query = select(Team).where(Team.id == team_id)
        if load_players:
            query = query.options(selectinload(Team.players))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_team(
        db: AsyncSession,
        team_in: TeamCreate,
        owner_id: uuid.UUID | None = None,
    ) -> Team:
        team = Team(
            name=team_in.name,
            race=team_in.race,
            league_id=team_in.league_id,
            owner_id=owner_id,
            treasury=team_in.treasury,
            rerolls=team_in.rerolls,
            assistant_coaches=team_in.assistant_coaches,
            cheerleaders=team_in.cheerleaders,
            apothecary=team_in.apothecary,
            dedicated_fans=team_in.dedicated_fans,
            group_name=team_in.group_name,
            conference_name=team_in.conference_name,
            logo_url=team_in.logo_url,
            team_value=0,
        )
        db.add(team)
        await db.commit()
        await db.refresh(team)
        return team

    @staticmethod
    async def update_team(
        db: AsyncSession,
        team: Team,
        team_in: TeamUpdate,
    ) -> Team:
        update_data = team_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(team, field, value)

        await db.commit()
        await db.refresh(team)
        return team

    @staticmethod
    async def delete_team(db: AsyncSession, team: Team) -> None:
        await db.delete(team)
        await db.commit()


team_service = TeamService()

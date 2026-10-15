import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.player import Player
from src.app.models.team import Team
from src.app.modules.players.schemas import PlayerAdvancement, PlayerCreate, PlayerUpdate
from src.app.modules.reference_data.service import reference_data_service


class PlayerService:
    @staticmethod
    async def list_players_by_team(db: AsyncSession, team_id: uuid.UUID) -> list[Player]:
        query = select(Player).where(Player.team_id == team_id).order_by(Player.number)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_player(db: AsyncSession, player_id: uuid.UUID) -> Player | None:
        query = select(Player).where(Player.id == player_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_player(db: AsyncSession, player_in: PlayerCreate) -> Player:
        player = Player(
            team_id=player_in.team_id,
            name=player_in.name,
            number=player_in.number,
            position=player_in.position,
            cost=player_in.cost,
            ma=player_in.ma,
            st=player_in.st,
            ag=player_in.ag,
            pa=player_in.pa,
            av=player_in.av,
            status=player_in.status,
            is_captain=player_in.is_captain,
            is_veteran=player_in.is_veteran,
        )
        db.add(player)

        # Update team value and deduct cost from treasury if team exists
        team = await db.get(Team, player_in.team_id)
        if team:
            if team.treasury is not None and team.treasury >= player_in.cost:
                team.treasury -= player_in.cost
            team.team_value = (team.team_value or 0) + player_in.cost

        await db.commit()
        await db.refresh(player)
        return player

    @staticmethod
    async def update_player(
        db: AsyncSession,
        player: Player,
        player_in: PlayerUpdate,
    ) -> Player:
        update_data = player_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(player, field, value)

        await db.commit()
        await db.refresh(player)
        return player

    @staticmethod
    async def add_advancement(
        db: AsyncSession,
        player: Player,
        adv: PlayerAdvancement,
    ) -> Player:
        # Business Rule: If skill is Elite in reference_data, TV cost is directly 30,000
        is_elite = reference_data_service.is_elite_skill(adv.skill) or adv.type == "elite"
        effective_tv_cost = 30000 if is_elite else adv.tv_cost

        current_advancements = list(player.advancements or [])
        adv_entry = adv.model_dump()
        adv_entry["tv_cost"] = effective_tv_cost
        current_advancements.append(adv_entry)
        player.advancements = current_advancements

        # Deduct SPP and increment TV added
        player.spp_spent = (player.spp_spent or 0) + adv.spp_cost
        player.tv_added = (player.tv_added or 0) + effective_tv_cost

        # Update team TV if player has a team
        if player.team_id:
            team = await db.get(Team, player.team_id)
            if team:
                team.team_value = (team.team_value or 0) + effective_tv_cost

        await db.commit()
        await db.refresh(player)
        return player

    @staticmethod
    async def delete_player(db: AsyncSession, player: Player) -> None:
        if player.team_id:
            team = await db.get(Team, player.team_id)
            if team:
                player_total_value = player.cost + (player.tv_added or 0)
                team.team_value = max(0, (team.team_value or 0) - player_total_value)

        await db.delete(player)
        await db.commit()


player_service = PlayerService()

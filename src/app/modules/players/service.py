import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.player import Player
from src.app.models.team import Team
from src.app.modules.players.schemas import PlayerAdvancement, PlayerCreate, PlayerUpdate
from src.app.modules.reference_data.service import reference_data_service

SPP_ADVANCEMENT_TABLE: dict[int, dict[str, int]] = {
    0: {"random_primary": 3, "primary": 6, "random_secondary": 6, "secondary": 12, "stat": 18},
    1: {"random_primary": 4, "primary": 8, "random_secondary": 8, "secondary": 14, "stat": 20},
    2: {"random_primary": 6, "primary": 12, "random_secondary": 12, "secondary": 18, "stat": 24},
    3: {"random_primary": 8, "primary": 16, "random_secondary": 16, "secondary": 22, "stat": 28},
    4: {"random_primary": 10, "primary": 20, "random_secondary": 20, "secondary": 26, "stat": 32},
    5: {"random_primary": 15, "primary": 30, "random_secondary": 30, "secondary": 40, "stat": 50},
}

STAT_TV_COST_MAP: dict[str, int] = {
    "MA": 20000,
    "AV": 10000,
    "PA": 20000,
    "AG": 40000,
    "ST": 80000,
}


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
    def calculate_advancement_costs(
        player: Player,
        adv: PlayerAdvancement,
    ) -> tuple[int, int]:
        """Calculates (effective_tv_cost, effective_spp_cost) for a player advancement.

        Applies manual overrides if passed in adv, otherwise computes:
        - TV Cost:
            - Stat: according to stat (MA: 20k, AV: 10k, PA: 20k, AG: 40k, ST: 80k)
            - Elite Skill: 30,000
            - Secondary Skill: 40,000
            - Random Secondary: 20,000
            - Random Primary: 10,000
            - Primary Skill: 20,000
        - SPP Cost:
            - Computed from official Blood Bowl tier progression table based on
              the number of existing advancements the player has (tier 0 to 5+).
        """
        # 1. Determine effective TV cost
        if adv.tv_cost is not None:
            effective_tv = adv.tv_cost
        elif adv.type == "stat":
            stat_name = (adv.stat or "").strip().upper()
            effective_tv = STAT_TV_COST_MAP.get(stat_name, 20000)
        elif reference_data_service.is_elite_skill(adv.skill):
            effective_tv = 30000
        elif adv.type == "secondary":
            effective_tv = 40000
        elif adv.type == "random_secondary":
            effective_tv = 20000
        elif adv.type in ("random_primary", "random"):
            effective_tv = 10000
        else:
            effective_tv = 20000

        # 2. Determine effective SPP cost
        if adv.spp_cost is not None:
            effective_spp = adv.spp_cost
        else:
            tier = min(len(player.advancements or []), 5)
            tier_dict = SPP_ADVANCEMENT_TABLE[tier]
            adv_type = (adv.type or "primary").strip().lower()
            if adv_type in ("random", "random_primary"):
                effective_spp = tier_dict["random_primary"]
            elif adv_type == "random_secondary":
                effective_spp = tier_dict["random_secondary"]
            elif adv_type == "secondary":
                effective_spp = tier_dict["secondary"]
            elif adv_type == "stat":
                effective_spp = tier_dict["stat"]
            else:
                effective_spp = tier_dict["primary"]

        return effective_tv, effective_spp

    @staticmethod
    async def add_advancement(
        db: AsyncSession,
        player: Player,
        adv: PlayerAdvancement,
        effective_tv_cost: int | None = None,
        effective_spp_cost: int | None = None,
    ) -> Player:
        if effective_tv_cost is None or effective_spp_cost is None:
            calc_tv, calc_spp = PlayerService.calculate_advancement_costs(player, adv)
            if effective_tv_cost is None:
                effective_tv_cost = calc_tv
            if effective_spp_cost is None:
                effective_spp_cost = calc_spp

        current_advancements = list(player.advancements or [])
        adv_entry = adv.model_dump()
        adv_entry["tv_cost"] = effective_tv_cost
        adv_entry["spp_cost"] = effective_spp_cost
        current_advancements.append(adv_entry)
        player.advancements = current_advancements

        # Apply stat modifications if applicable
        if adv.type == "stat" and adv.stat:
            stat_name = adv.stat.strip().upper()
            if stat_name == "MA":
                player.ma_mod = (player.ma_mod or 0) + 1
                if player.ma is not None:
                    player.ma += 1
            elif stat_name == "ST":
                player.st_mod = (player.st_mod or 0) + 1
                if player.st is not None:
                    player.st += 1
            elif stat_name == "AG":
                player.ag_mod = (player.ag_mod or 0) + 1
            elif stat_name == "PA":
                player.pa_mod = (player.pa_mod or 0) + 1
            elif stat_name == "AV":
                player.av_mod = (player.av_mod or 0) + 1

        # Deduct SPP and increment TV added
        player.spp_spent = (player.spp_spent or 0) + effective_spp_cost
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

import random
import secrets
import uuid
from datetime import date, timedelta
from typing import Any
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.core.exceptions import EntityNotFoundException, RuleViolationException
from src.app.models.league import League, LeagueMember, LeagueRound
from src.app.models.match import Match
from src.app.models.team import Team
from src.app.modules.leagues.schemas import (
    LeagueCreate,
    LeagueRoundDetailResponse,
    LeagueRoundUpdate,
    LeagueUpdate,
    PlayoffGenerateRequest,
    PlayoffGenerateResponse,
    ScheduleGenerateRequest,
    ScheduleGenerateResponse,
)
from src.app.modules.matches.service import match_service


def generate_invite_code(length: int = 6) -> str:
    """Generates an uppercase alphanumeric code without confusing characters (0/O, 1/I)."""
    safe_chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    code = "".join(secrets.choice(safe_chars) for _ in range(length))
    return f"BB-{code}"


def sort_teams_by_standing(teams: list[Team]) -> list[Team]:
    """Sorts teams according to official Blood Bowl / Fantasy Football tiebreaker rules:
    1. Points (3 for win, 1 for draw, 0 for loss)
    2. Net Touchdown difference (TD for - TD against)
    3. Touchdowns scored (TD for)
    4. Net Casualty difference (CAS for - CAS against)
    5. Casualties caused (CAS for)
    6. Lower Team Value (TV)
    """
    def rank_key(t: Team):
        pts = (t.wins or 0) * 3 + (t.draws or 0)
        td_diff = (t.td_for or 0) - (t.td_against or 0)
        td_for = t.td_for or 0
        cas_diff = (t.cas_for or 0) - (t.cas_against or 0)
        cas_for = t.cas_for or 0
        tv = -(t.team_value or 0)
        return (pts, td_diff, td_for, cas_diff, cas_for, tv)

    return sorted(teams, key=rank_key, reverse=True)


def generate_round_robin_pairings(
    team_ids: list[uuid.UUID],
    is_double_round: bool = False,
    existing_rounds_count: int = 0,
    round_name_prefix: str = "Jornada",
    phase: int = 1,
    start_date: date | None = None,
    round_interval_days: int = 7,
) -> list[dict[str, Any]]:
    working_ids: list[uuid.UUID | None] = list(team_ids)
    if len(working_ids) % 2 != 0:
        working_ids.append(None)  # None represents BYE week

    n = len(working_ids)
    rounds_count = n - 1
    matches_per_round = n // 2

    first_half_rounds: list[dict[str, Any]] = []

    for r in range(rounds_count):
        r_num = existing_rounds_count + r + 1
        r_matches: list[tuple[uuid.UUID, uuid.UUID]] = []
        for i in range(matches_per_round):
            home = working_ids[i]
            away = working_ids[n - 1 - i]
            if home is not None and away is not None:
                # Alternate home/away for the fixed team on alternating rounds for fairness
                if r % 2 == 1 and i == 0:
                    r_matches.append((away, home))
                else:
                    r_matches.append((home, away))

        r_start = (
            start_date + timedelta(days=r * round_interval_days)
            if start_date
            else None
        )
        r_end = (
            r_start + timedelta(days=round_interval_days - 1)
            if r_start
            else None
        )

        first_half_rounds.append({
            "round_number": r_num,
            "name": f"{round_name_prefix} {r_num}",
            "phase": phase,
            "start_date": r_start,
            "end_date": r_end,
            "matches": r_matches,
        })

        # Rotate circle (fix working_ids[0], rotate working_ids[1..n-1])
        last = working_ids.pop()
        working_ids.insert(1, last)

    all_rounds = list(first_half_rounds)

    if is_double_round:
        for idx, r_data in enumerate(first_half_rounds):
            r_num = existing_rounds_count + rounds_count + idx + 1
            r_start = (
                start_date + timedelta(days=(rounds_count + idx) * round_interval_days)
                if start_date
                else None
            )
            r_end = (
                r_start + timedelta(days=round_interval_days - 1)
                if r_start
                else None
            )
            all_rounds.append({
                "round_number": r_num,
                "name": f"{round_name_prefix} {r_num}",
                "phase": phase,
                "start_date": r_start,
                "end_date": r_end,
                "matches": [(away, home) for home, away in r_data["matches"]],
            })

    return all_rounds


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
            if load_teams and "teams" in league.__dict__ and league.teams is not None:
                league.teams_count = len(league.teams)
            else:
                league.teams_count = 0
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
            if load_teams and "teams" in league.__dict__ and league.teams is not None:
                league.teams_count = len(league.teams)
            else:
                league.teams_count = 0
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
        league.teams_count = len(league.teams) if ("teams" in league.__dict__ and league.teams is not None) else 0
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
        user_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
    ) -> League:
        """Enrolls a coach and optionally an existing team into the league."""
        # 1. If user_id provided, check and add league membership
        if user_id:
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
        return await LeagueService.get_league(db, league.id, load_teams=True) or league

    @staticmethod
    def _to_round_detail_response(round_obj: LeagueRound) -> LeagueRoundDetailResponse:
        match_responses = []
        completed_count = 0
        if round_obj.matches:
            for m in round_obj.matches:
                resp = match_service._to_match_response(m)
                match_responses.append(resp)
                if m.status in ("completed", "validated"):
                    completed_count += 1

        return LeagueRoundDetailResponse(
            id=round_obj.id,
            league_id=round_obj.league_id,
            round_number=round_obj.round_number,
            name=round_obj.name,
            phase=round_obj.phase,
            start_date=round_obj.start_date,
            end_date=round_obj.end_date,
            extension_days=round_obj.extension_days,
            created_at=round_obj.created_at,
            matches=match_responses,
            matches_count=len(match_responses),
            completed_matches_count=completed_count,
        )

    @staticmethod
    async def list_rounds(
        db: AsyncSession,
        league_id: uuid.UUID,
        phase: int | None = None,
    ) -> list[LeagueRoundDetailResponse]:
        """Lists all rounds for a league with their associated matches and team names."""
        query = (
            select(LeagueRound)
            .where(LeagueRound.league_id == league_id)
            .options(
                selectinload(LeagueRound.matches).selectinload(Match.home_team),
                selectinload(LeagueRound.matches).selectinload(Match.away_team),
            )
            .order_by(LeagueRound.round_number)
        )
        if phase is not None:
            query = query.where(LeagueRound.phase == phase)

        result = await db.execute(query)
        rounds = list(result.scalars().all())
        return [LeagueService._to_round_detail_response(r) for r in rounds]

    @staticmethod
    async def get_round(
        db: AsyncSession,
        round_id: uuid.UUID,
    ) -> LeagueRound | None:
        """Retrieves a single round with matches and team details."""
        query = (
            select(LeagueRound)
            .where(LeagueRound.id == round_id)
            .options(
                selectinload(LeagueRound.matches).selectinload(Match.home_team),
                selectinload(LeagueRound.matches).selectinload(Match.away_team),
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_round(
        db: AsyncSession,
        round_obj: LeagueRound,
        update_in: LeagueRoundUpdate,
    ) -> LeagueRoundDetailResponse:
        """Updates round dates, extension days, phase, or name."""
        update_data = update_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(round_obj, field, value)

        await db.commit()
        refreshed = await LeagueService.get_round(db, round_obj.id)
        return LeagueService._to_round_detail_response(refreshed or round_obj)

    @staticmethod
    async def delete_round(
        db: AsyncSession,
        round_obj: LeagueRound,
    ) -> None:
        """Deletes a round and its scheduled matches, ensuring no completed matches exist."""
        if round_obj.matches:
            for m in round_obj.matches:
                if m.status in ("completed", "validated"):
                    raise RuleViolationException(
                        "No se puede eliminar la jornada porque contiene partidos ya completados."
                    )
        await db.delete(round_obj)
        await db.commit()

    @staticmethod
    async def generate_schedule(
        db: AsyncSession,
        league: League,
        req: ScheduleGenerateRequest,
    ) -> ScheduleGenerateResponse:
        """Generates rounds and match schedule for a league in round-robin, groups, or manual format."""
        # 1. Fetch enrolled teams
        team_stmt = select(Team).where(Team.league_id == league.id)
        teams = list((await db.execute(team_stmt)).scalars().all())

        if req.format != "custom_manual" and len(teams) < 2:
            raise RuleViolationException(
                f"Se necesitan al menos 2 equipos inscritos en la liga para generar el calendario. Equipos actuales: {len(teams)}."
            )

        # 2. Check existing rounds & replace option
        existing_rounds_query = (
            select(LeagueRound)
            .where(LeagueRound.league_id == league.id)
            .options(selectinload(LeagueRound.matches))
        )
        existing_rounds = list((await db.execute(existing_rounds_query)).scalars().all())

        existing_rounds_count = 0
        if existing_rounds:
            if req.replace_existing:
                for r in existing_rounds:
                    if r.matches:
                        for m in r.matches:
                            if m.status in ("completed", "validated"):
                                raise RuleViolationException(
                                    "No se puede reemplazar el calendario porque ya existen partidos disputados o completados."
                                )
                # Safe to delete previous matches and rounds
                await db.execute(delete(Match).where(Match.league_id == league.id))
                await db.execute(delete(LeagueRound).where(LeagueRound.league_id == league.id))
                await db.flush()
                existing_rounds_count = 0
            else:
                existing_rounds_count = max(r.round_number for r in existing_rounds)

        rounds_to_create: list[dict[str, Any]] = []

        # 3. Handle Formats
        if req.format == "custom_manual":
            if not req.custom_rounds:
                raise RuleViolationException("Debes proporcionar al menos una jornada en el modo custom_manual.")

            for cr_idx, cr in enumerate(req.custom_rounds):
                r_num = cr.number or (existing_rounds_count + cr_idx + 1)
                r_matches = []
                for m in cr.matches:
                    if m.home_team_id == m.away_team_id:
                        raise RuleViolationException(
                            f"Un equipo no puede jugar contra sí mismo en la {cr.name or f'Jornada {r_num}'}."
                        )
                    r_matches.append((m.home_team_id, m.away_team_id))

                rounds_to_create.append({
                    "round_number": r_num,
                    "name": cr.name or f"Jornada {r_num}",
                    "phase": cr.phase,
                    "start_date": cr.start_date,
                    "end_date": cr.end_date,
                    "matches": r_matches,
                })

        elif req.format == "round_robin":
            team_ids = [t.id for t in teams]
            rounds_to_create = generate_round_robin_pairings(
                team_ids=team_ids,
                is_double_round=req.is_double_round or league.is_double_round,
                existing_rounds_count=existing_rounds_count,
                round_name_prefix="Jornada",
                phase=1,
                start_date=req.start_date,
                round_interval_days=req.round_interval_days,
            )

        elif req.format == "groups_playoffs":
            num_groups = max(2, req.number_of_groups or league.number_of_groups or 2)
            group_teams: dict[str, list[uuid.UUID]] = {}

            if req.assignment_mode == "manual" and req.team_assignments:
                for t in teams:
                    asg = req.team_assignments.get(str(t.id), {})
                    grp = asg.get("group", "A")
                    t.group_name = grp
                    t.conference_name = None
                    group_teams.setdefault(grp, []).append(t.id)
            else:
                shuffled = list(teams)
                random.shuffle(shuffled)
                for idx, t in enumerate(shuffled):
                    grp = chr(65 + (idx % num_groups))
                    t.group_name = grp
                    t.conference_name = None
                    group_teams.setdefault(grp, []).append(t.id)

            for grp, t_ids in group_teams.items():
                if len(t_ids) < 2:
                    raise RuleViolationException(
                        f"El Grupo {grp} tiene menos de 2 equipos ({len(t_ids)}). Cada grupo necesita al menos 2 equipos para disputar encuentros."
                    )

            for grp, t_ids in sorted(group_teams.items()):
                grp_rounds = generate_round_robin_pairings(
                    team_ids=t_ids,
                    is_double_round=req.is_double_round or league.is_double_round,
                    existing_rounds_count=existing_rounds_count,
                    round_name_prefix=f"Grupo {grp} - Jornada",
                    phase=1,
                    start_date=req.start_date,
                    round_interval_days=req.round_interval_days,
                )
                rounds_to_create.extend(grp_rounds)

        elif req.format == "conferences_groups":
            num_groups = max(1, req.number_of_groups or 2)
            conf_group_teams: dict[str, list[uuid.UUID]] = {}

            if req.assignment_mode == "manual" and req.team_assignments:
                for t in teams:
                    asg = req.team_assignments.get(str(t.id), {})
                    conf = asg.get("conf", "Este")
                    grp = asg.get("group", "A")
                    t.conference_name = conf
                    t.group_name = grp
                    conf_group_teams.setdefault(f"{conf}_{grp}", []).append(t.id)
            else:
                shuffled = list(teams)
                random.shuffle(shuffled)
                for idx, t in enumerate(shuffled):
                    conf = "Este" if idx % 2 == 0 else "Oeste"
                    conf_index = idx // 2
                    conf_offset = num_groups if conf == "Oeste" else 0
                    grp = chr(65 + conf_offset + (conf_index % num_groups))
                    t.conference_name = conf
                    t.group_name = grp
                    conf_group_teams.setdefault(f"{conf}_{grp}", []).append(t.id)

            for key, t_ids in sorted(conf_group_teams.items()):
                conf, grp = key.split("_")
                if len(t_ids) < 2:
                    raise RuleViolationException(
                        f"La Conferencia {conf} - Grupo {grp} tiene menos de 2 equipos ({len(t_ids)})."
                    )
                c_rounds = generate_round_robin_pairings(
                    team_ids=t_ids,
                    is_double_round=req.is_double_round or league.is_double_round,
                    existing_rounds_count=existing_rounds_count,
                    round_name_prefix=f"Conf. {conf} - Grupo {grp} - Jornada",
                    phase=1,
                    start_date=req.start_date,
                    round_interval_days=req.round_interval_days,
                )
                rounds_to_create.extend(c_rounds)

        else:
            raise RuleViolationException(f"Formato de calendario '{req.format}' no soportado.")

        # 4. Insert rounds and matches into database
        created_round_ids: list[uuid.UUID] = []
        total_matches = 0

        for r_info in rounds_to_create:
            new_round = LeagueRound(
                league_id=league.id,
                round_number=r_info["round_number"],
                name=r_info["name"],
                phase=r_info["phase"],
                start_date=r_info["start_date"],
                end_date=r_info["end_date"],
            )
            db.add(new_round)
            await db.flush()
            created_round_ids.append(new_round.id)

            for home_id, away_id in r_info["matches"]:
                match_obj = Match(
                    league_id=league.id,
                    round_id=new_round.id,
                    home_team_id=home_id,
                    away_team_id=away_id,
                    status="scheduled",
                )
                db.add(match_obj)
                total_matches += 1

        if league.status == "draft":
            league.status = "active"

        await db.commit()

        # 5. Fetch details
        created_rounds_detail: list[LeagueRoundDetailResponse] = []
        for r_id in created_round_ids:
            round_obj = await LeagueService.get_round(db, r_id)
            if round_obj:
                created_rounds_detail.append(LeagueService._to_round_detail_response(round_obj))

        return ScheduleGenerateResponse(
            league_id=league.id,
            format=req.format,
            rounds_created=len(created_round_ids),
            matches_created=total_matches,
            rounds=created_rounds_detail,
        )

    @staticmethod
    async def generate_playoffs(
        db: AsyncSession,
        league: League,
        req: PlayoffGenerateRequest,
    ) -> PlayoffGenerateResponse:
        """Generates single-elimination or double-elimination playoff brackets based on league standings."""
        # 1. Fetch teams enrolled in the league
        team_stmt = select(Team).where(Team.league_id == league.id)
        teams = list((await db.execute(team_stmt)).scalars().all())

        if req.qualified_team_ids:
            team_map = {t.id: t for t in teams}
            ranked = [team_map[tid] for tid in req.qualified_team_ids if tid in team_map]
        else:
            ranked = sort_teams_by_standing(teams)

        matches_to_create: list[tuple[uuid.UUID, uuid.UUID]] = []
        default_round_num = 100
        default_name = "Playoffs"

        if req.format == "final_directa":
            if len(ranked) < 2:
                raise RuleViolationException("Se necesitan al menos 2 equipos para la Final Directa.")
            default_round_num = 102
            default_name = "Playoffs - Gran Final"
            matches_to_create.append((ranked[0].id, ranked[1].id))

        elif req.format == "semis":
            if len(ranked) < 4:
                raise RuleViolationException(
                    f"Se necesitan al menos 4 equipos para Semifinales. Equipos disponibles: {len(ranked)}."
                )
            default_round_num = 101
            default_name = "Playoffs - Semifinales"
            matches_to_create.append((ranked[0].id, ranked[3].id))
            matches_to_create.append((ranked[1].id, ranked[2].id))

        elif req.format == "cuartos":
            if len(ranked) < 8:
                raise RuleViolationException(
                    f"Se necesitan al menos 8 equipos para Cuartos de Final. Equipos disponibles: {len(ranked)}."
                )
            default_round_num = 100
            default_name = "Playoffs - Cuartos de Final"
            matches_to_create.append((ranked[0].id, ranked[7].id))
            matches_to_create.append((ranked[1].id, ranked[6].id))
            matches_to_create.append((ranked[2].id, ranked[5].id))
            matches_to_create.append((ranked[3].id, ranked[4].id))

        elif req.format == "doble_elim":
            if len(ranked) < 4:
                raise RuleViolationException(
                    f"Se necesitan al menos 4 equipos para Doble Eliminación. Equipos disponibles: {len(ranked)}."
                )
            default_round_num = 201
            default_name = "Playoffs Doble - R1 Ganadores"
            matches_to_create.append((ranked[0].id, ranked[3].id))
            matches_to_create.append((ranked[1].id, ranked[2].id))

        else:
            raise RuleViolationException(f"Formato de playoff '{req.format}' no soportado.")

        round_num = req.round_number or default_round_num
        round_name = req.name or default_name

        playoff_round = LeagueRound(
            league_id=league.id,
            round_number=round_num,
            name=round_name,
            phase=req.phase,
            start_date=req.start_date,
            end_date=req.end_date,
        )
        db.add(playoff_round)
        await db.flush()

        for home_id, away_id in matches_to_create:
            match_obj = Match(
                league_id=league.id,
                round_id=playoff_round.id,
                home_team_id=home_id,
                away_team_id=away_id,
                status="scheduled",
            )
            db.add(match_obj)

        if league.current_phase < req.phase:
            league.current_phase = req.phase

        await db.commit()

        refreshed = await LeagueService.get_round(db, playoff_round.id)
        detail = LeagueService._to_round_detail_response(refreshed or playoff_round)

        return PlayoffGenerateResponse(
            league_id=league.id,
            format=req.format,
            round=detail,
        )

league_service = LeagueService()

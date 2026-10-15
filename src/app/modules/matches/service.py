import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.core.exceptions import EntityNotFoundException, RuleViolationException
from src.app.models.match import Match, MatchPlayerEvent
from src.app.models.player import Player
from src.app.models.team import Team
from src.app.modules.matches.schemas import (
    MatchCreate,
    MatchDetailResponse,
    MatchResponse,
    MatchResultSubmit,
    MatchUpdate,
    PlayerEventResponse,
)


def calculate_spp(
    touchdowns: int = 0,
    casualties_caused: int = 0,
    completions: int = 0,
    superb_passes: int = 0,
    interceptions: int = 0,
    is_mvp: bool = False,
) -> int:
    """Calculates Star Player Points (SPP) according to Official Blood Bowl 2020 rules:
    - Touchdown: 3 SPP
    - Casualty: 2 SPP
    - Completion: 1 SPP
    - Superb Pass: 1 SPP
    - Interception: 2 SPP
    - MVP: 4 SPP
    """
    spp = 0
    spp += touchdowns * 3
    spp += casualties_caused * 2
    spp += completions * 1
    spp += superb_passes * 1
    spp += interceptions * 2
    if is_mvp:
        spp += 4
    return spp


class MatchService:
    @staticmethod
    def _to_match_response(match: Match) -> MatchResponse:
        return MatchResponse(
            id=match.id,
            league_id=match.league_id,
            round_id=match.round_id,
            tournament_id=match.tournament_id,
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id,
            home_team_name=match.home_team.name if match.home_team else None,
            away_team_name=match.away_team.name if match.away_team else None,
            home_score=match.home_score,
            away_score=match.away_score,
            status=match.status,
            weather=match.weather,
            kickoff_event=match.kickoff_event,
            home_fame=match.home_fame,
            away_fame=match.away_fame,
            home_winnings=match.home_winnings,
            away_winnings=match.away_winnings,
            home_mistake_loss=match.home_mistake_loss,
            away_mistake_loss=match.away_mistake_loss,
            home_initial_treasury=match.home_initial_treasury,
            away_initial_treasury=match.away_initial_treasury,
            home_tv=match.home_tv,
            away_tv=match.away_tv,
            home_inducements=match.home_inducements or {},
            away_inducements=match.away_inducements or {},
            played_at=match.played_at,
            wizard_step=match.wizard_step,
            updated_at=match.updated_at,
        )

    @staticmethod
    def _to_match_detail_response(match: Match) -> MatchDetailResponse:
        base_resp = MatchService._to_match_response(match)

        events_list: list[PlayerEventResponse] = []
        if match.player_events:
            for pe in match.player_events:
                spp = calculate_spp(
                    touchdowns=pe.touchdowns,
                    casualties_caused=pe.casualties_caused,
                    completions=pe.completions,
                    superb_passes=pe.superb_passes,
                    interceptions=pe.interceptions,
                    is_mvp=pe.is_mvp,
                )
                player_name = pe.player.name if pe.player else None
                player_number = pe.player.number if pe.player else None
                player_position = pe.player.position if pe.player else None

                events_list.append(
                    PlayerEventResponse(
                        id=pe.id,
                        match_id=pe.match_id,
                        player_id=pe.player_id,
                        team_id=pe.team_id,
                        touchdowns=pe.touchdowns,
                        completions=pe.completions,
                        casualties_caused=pe.casualties_caused,
                        interceptions=pe.interceptions,
                        superb_passes=pe.superb_passes,
                        is_mvp=pe.is_mvp,
                        injury_result=pe.injury_result,
                        fouls_committed=pe.fouls_committed or 0,
                        sprint_falls=pe.sprint_falls or 0,
                        spp_earned=spp,
                        player_name=player_name,
                        player_number=player_number,
                        player_position=player_position,
                    )
                )

        return MatchDetailResponse(
            **base_resp.model_dump(),
            player_events=events_list,
            wizard_data=match.wizard_data or {},
        )

    @staticmethod
    async def list_matches(
        db: AsyncSession,
        league_id: uuid.UUID | None = None,
        round_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[MatchResponse]:
        """Lists matches with optional filtering by league, round, participating team, or status."""
        query = (
            select(Match)
            .options(selectinload(Match.home_team), selectinload(Match.away_team))
            .order_by(Match.played_at.desc())
        )

        if league_id:
            query = query.where(Match.league_id == league_id)
        if round_id:
            query = query.where(Match.round_id == round_id)
        if status:
            query = query.where(Match.status == status)
        if team_id:
            query = query.where(or_(Match.home_team_id == team_id, Match.away_team_id == team_id))

        result = await db.execute(query)
        matches = list(result.scalars().all())
        return [MatchService._to_match_response(m) for m in matches]

    @staticmethod
    async def get_match(
        db: AsyncSession,
        match_id: uuid.UUID,
        load_details: bool = False,
    ) -> Match | None:
        """Retrieves a single match by ID."""
        query = select(Match).where(Match.id == match_id).options(
            selectinload(Match.home_team),
            selectinload(Match.away_team),
        )

        if load_details:
            query = query.options(
                selectinload(Match.player_events).selectinload(MatchPlayerEvent.player)
            )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_match(
        db: AsyncSession,
        match_in: MatchCreate,
        creator_id: uuid.UUID | None = None,
    ) -> MatchResponse:
        """Schedules a new match between two teams."""
        if match_in.home_team_id == match_in.away_team_id:
            raise RuleViolationException("A team cannot play a match against itself.")

        # Validate home team
        home_team = (
            await db.execute(select(Team).where(Team.id == match_in.home_team_id))
        ).scalar_one_or_none()
        if not home_team:
            raise EntityNotFoundException("Home Team", match_in.home_team_id)

        # Validate away team
        away_team = (
            await db.execute(select(Team).where(Team.id == match_in.away_team_id))
        ).scalar_one_or_none()
        if not away_team:
            raise EntityNotFoundException("Away Team", match_in.away_team_id)

        match = Match(
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            league_id=match_in.league_id,
            round_id=match_in.round_id,
            tournament_id=match_in.tournament_id,
            played_at=match_in.played_at or datetime.utcnow(),
            status="scheduled",
            weather=match_in.weather,
            kickoff_event=match_in.kickoff_event,
            home_tv=match_in.home_tv or home_team.team_value or 0,
            away_tv=match_in.away_tv or away_team.team_value or 0,
            home_initial_treasury=home_team.treasury or 0,
            away_initial_treasury=away_team.treasury or 0,
            home_inducements=match_in.home_inducements or {},
            away_inducements=match_in.away_inducements or {},
            creator_id=creator_id,
        )
        db.add(match)
        await db.commit()

        # Reload with relationships
        loaded_match = await MatchService.get_match(db, match.id)
        return MatchService._to_match_response(loaded_match or match)

    @staticmethod
    async def update_match(
        db: AsyncSession,
        match: Match,
        match_in: MatchUpdate,
    ) -> MatchResponse:
        """Updates match status, wizard step, or pre-match settings."""
        update_data = match_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(match, field, value)

        await db.commit()
        loaded = await MatchService.get_match(db, match.id)
        return MatchService._to_match_response(loaded or match)

    @staticmethod
    async def record_match_result(
        db: AsyncSession,
        match: Match,
        result_in: MatchResultSubmit,
    ) -> MatchDetailResponse:
        """Records final match score, player stats (TDs, CAS, COMPs, MVPs), calculates SPP,
        updates player injuries, and updates team standings and treasuries.
        """
        if match.status in ("completed", "validated"):
            raise RuleViolationException(
                f"Match is already marked as {match.status}. Cannot re-submit result."
            )

        # 1. Update match scores and final post-match data
        match.home_score = result_in.home_score
        match.away_score = result_in.away_score
        match.status = "completed"
        if result_in.weather:
            match.weather = result_in.weather
        if result_in.kickoff_event:
            match.kickoff_event = result_in.kickoff_event
        match.home_fame = result_in.home_fame
        match.away_fame = result_in.away_fame
        match.home_winnings = result_in.home_winnings
        match.away_winnings = result_in.away_winnings
        match.home_mistake_loss = result_in.home_mistake_loss
        match.away_mistake_loss = result_in.away_mistake_loss

        # 2. Process player events
        home_cas_total = 0
        away_cas_total = 0
        home_fouls_total = 0
        away_fouls_total = 0

        for pe_in in result_in.player_events:
            # Create MatchPlayerEvent record
            event_record = MatchPlayerEvent(
                match_id=match.id,
                player_id=pe_in.player_id,
                team_id=pe_in.team_id,
                touchdowns=pe_in.touchdowns,
                completions=pe_in.completions,
                casualties_caused=pe_in.casualties_caused,
                interceptions=pe_in.interceptions,
                superb_passes=pe_in.superb_passes,
                is_mvp=pe_in.is_mvp,
                injury_result=pe_in.injury_result,
                fouls_committed=pe_in.fouls_committed,
                sprint_falls=pe_in.sprint_falls,
            )
            db.add(event_record)

            # Track team totals
            if pe_in.team_id == match.home_team_id:
                home_cas_total += pe_in.casualties_caused
                home_fouls_total += pe_in.fouls_committed
            elif pe_in.team_id == match.away_team_id:
                away_cas_total += pe_in.casualties_caused
                away_fouls_total += pe_in.fouls_committed

            # Award SPP and update Player
            player = (
                await db.execute(select(Player).where(Player.id == pe_in.player_id))
            ).scalar_one_or_none()

            if player:
                spp_gained = calculate_spp(
                    touchdowns=pe_in.touchdowns,
                    casualties_caused=pe_in.casualties_caused,
                    completions=pe_in.completions,
                    superb_passes=pe_in.superb_passes,
                    interceptions=pe_in.interceptions,
                    is_mvp=pe_in.is_mvp,
                )
                player.spp = (player.spp or 0) + spp_gained
                player.fouls_committed = (player.fouls_committed or 0) + pe_in.fouls_committed
                player.sprint_falls = (player.sprint_falls or 0) + pe_in.sprint_falls

                # Apply injury effects
                if pe_in.injury_result:
                    inj = pe_in.injury_result.strip().lower()
                    if inj == "mng":
                        player.status = "mng"
                    elif inj == "dead":
                        player.status = "dead"
                    elif inj == "niggling":
                        player.niggling = (player.niggling or 0) + 1
                    elif inj in ("-1_ma", "ma"):
                        player.ma_mod = (player.ma_mod or 0) - 1
                    elif inj in ("-1_st", "st"):
                        player.st_mod = (player.st_mod or 0) - 1
                    elif inj in ("-1_ag", "ag"):
                        player.ag_mod = (player.ag_mod or 0) - 1
                    elif inj in ("-1_pa", "pa"):
                        player.pa_mod = (player.pa_mod or 0) - 1
                    elif inj in ("-1_av", "av"):
                        player.av_mod = (player.av_mod or 0) - 1

        # 3. Update Home and Away Team stats
        home_team = (
            await db.execute(select(Team).where(Team.id == match.home_team_id))
        ).scalar_one_or_none()
        away_team = (
            await db.execute(select(Team).where(Team.id == match.away_team_id))
        ).scalar_one_or_none()

        if home_team and away_team:
            home_team.played = (home_team.played or 0) + 1
            away_team.played = (away_team.played or 0) + 1

            home_team.td_for = (home_team.td_for or 0) + match.home_score
            home_team.td_against = (home_team.td_against or 0) + match.away_score
            away_team.td_for = (away_team.td_for or 0) + match.away_score
            away_team.td_against = (away_team.td_against or 0) + match.home_score

            home_team.cas_for = (home_team.cas_for or 0) + home_cas_total
            home_team.cas_against = (home_team.cas_against or 0) + away_cas_total
            away_team.cas_for = (away_team.cas_for or 0) + away_cas_total
            away_team.cas_against = (away_team.cas_against or 0) + home_cas_total

            home_team.fouls_committed = (home_team.fouls_committed or 0) + home_fouls_total
            away_team.fouls_committed = (away_team.fouls_committed or 0) + away_fouls_total

            if match.home_score > match.away_score:
                home_team.wins = (home_team.wins or 0) + 1
                away_team.losses = (away_team.losses or 0) + 1
            elif match.away_score > match.home_score:
                away_team.wins = (away_team.wins or 0) + 1
                home_team.losses = (home_team.losses or 0) + 1
            else:
                home_team.draws = (home_team.draws or 0) + 1
                away_team.draws = (away_team.draws or 0) + 1

            # Update treasuries (winnings minus expensive mistake losses)
            net_home_winnings = max(0, match.home_winnings - match.home_mistake_loss)
            net_away_winnings = max(0, match.away_winnings - match.away_mistake_loss)
            home_team.treasury = (home_team.treasury or 0) + net_home_winnings
            away_team.treasury = (away_team.treasury or 0) + net_away_winnings

        await db.commit()

        # Reload with full relations
        reloaded = await MatchService.get_match(db, match.id, load_details=True)
        return MatchService._to_match_detail_response(reloaded or match)

    @staticmethod
    async def delete_match(db: AsyncSession, match: Match) -> None:
        """Deletes a match."""
        await db.delete(match)
        await db.commit()


match_service = MatchService()

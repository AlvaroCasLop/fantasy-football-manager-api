import uuid
from datetime import date
import pytest

from src.app.models.league import LeagueRound
from src.app.models.match import Match
from src.app.models.team import Team
from src.app.modules.leagues.schemas import (
    CustomMatchInput,
    CustomRoundInput,
    LeagueRoundDetailResponse,
    LeagueRoundResponse,
    LeagueRoundUpdate,
    PlayoffGenerateRequest,
    PlayoffGenerateResponse,
    ScheduleGenerateRequest,
    ScheduleGenerateResponse,
)
from src.app.modules.leagues.service import (
    generate_round_robin_pairings,
    sort_teams_by_standing,
)


def test_round_robin_pairings_even_teams():
    team_a = uuid.uuid4()
    team_b = uuid.uuid4()
    team_c = uuid.uuid4()
    team_d = uuid.uuid4()
    teams = [team_a, team_b, team_c, team_d]

    rounds = generate_round_robin_pairings(
        team_ids=teams,
        is_double_round=False,
        existing_rounds_count=0,
        round_name_prefix="Jornada",
        phase=1,
    )

    assert len(rounds) == 3
    # Check that each round has 2 matches
    for r in rounds:
        assert len(r["matches"]) == 2

    # Check that every pair of teams plays each other exactly once
    all_pairs = set()
    for r in rounds:
        for home, away in r["matches"]:
            assert home != away
            pair = tuple(sorted([str(home), str(away)]))
            assert pair not in all_pairs, f"Duplicate pairing found: {pair}"
            all_pairs.add(pair)

    assert len(all_pairs) == 6  # 4 * 3 / 2 = 6 unique match-ups


def test_round_robin_pairings_odd_teams():
    team_a = uuid.uuid4()
    team_b = uuid.uuid4()
    team_c = uuid.uuid4()
    teams = [team_a, team_b, team_c]

    rounds = generate_round_robin_pairings(
        team_ids=teams,
        is_double_round=False,
        existing_rounds_count=0,
        round_name_prefix="Jornada",
        phase=1,
    )

    # With 3 teams + 1 BYE, there are 3 rounds, each with 1 match
    assert len(rounds) == 3
    for r in rounds:
        assert len(r["matches"]) == 1

    all_pairs = set()
    for r in rounds:
        for home, away in r["matches"]:
            pair = tuple(sorted([str(home), str(away)]))
            all_pairs.add(pair)

    assert len(all_pairs) == 3  # 3 * 2 / 2 = 3 unique match-ups


def test_round_robin_double_round():
    team_a = uuid.uuid4()
    team_b = uuid.uuid4()
    team_c = uuid.uuid4()
    team_d = uuid.uuid4()
    teams = [team_a, team_b, team_c, team_d]

    rounds = generate_round_robin_pairings(
        team_ids=teams,
        is_double_round=True,
        existing_rounds_count=0,
        round_name_prefix="Jornada",
        phase=1,
    )

    assert len(rounds) == 6  # 3 single + 3 return leg

    first_half_matches = [r["matches"] for r in rounds[:3]]
    second_half_matches = [r["matches"] for r in rounds[3:]]

    # In second half, home and away must be inverted
    for r_idx in range(3):
        first_leg = first_half_matches[r_idx]
        second_leg = second_half_matches[r_idx]
        for m_idx in range(len(first_leg)):
            f_home, f_away = first_leg[m_idx]
            s_home, s_away = second_leg[m_idx]
            assert f_home == s_away
            assert f_away == s_home


def test_round_robin_with_dates():
    team_a = uuid.uuid4()
    team_b = uuid.uuid4()

    start_d = date(2026, 11, 1)
    rounds = generate_round_robin_pairings(
        team_ids=[team_a, team_b],
        is_double_round=True,
        existing_rounds_count=2,
        round_name_prefix="Jornada",
        phase=1,
        start_date=start_d,
        round_interval_days=7,
    )

    assert len(rounds) == 2
    assert rounds[0]["round_number"] == 3
    assert rounds[0]["start_date"] == date(2026, 11, 1)
    assert rounds[0]["end_date"] == date(2026, 11, 7)

    assert rounds[1]["round_number"] == 4
    assert rounds[1]["start_date"] == date(2026, 11, 8)
    assert rounds[1]["end_date"] == date(2026, 11, 14)


def test_sort_teams_by_standing():
    # Team 1: 3 wins = 9 pts
    t1 = Team(id=uuid.uuid4(), name="T1", wins=3, draws=0, td_for=6, td_against=2, cas_for=5, cas_against=1, team_value=1200000)
    # Team 2: 2 wins, 1 draw = 7 pts
    t2 = Team(id=uuid.uuid4(), name="T2", wins=2, draws=1, td_for=4, td_against=1, cas_for=3, cas_against=2, team_value=1100000)
    # Team 3: 2 wins, 0 draws = 6 pts (TD diff +5)
    t3 = Team(id=uuid.uuid4(), name="T3", wins=2, draws=0, td_for=7, td_against=2, cas_for=2, cas_against=2, team_value=1000000)
    # Team 4: 2 wins, 0 draws = 6 pts (TD diff +2)
    t4 = Team(id=uuid.uuid4(), name="T4", wins=2, draws=0, td_for=5, td_against=3, cas_for=1, cas_against=1, team_value=950000)

    ranked = sort_teams_by_standing([t4, t2, t1, t3])
    assert ranked[0].name == "T1"
    assert ranked[1].name == "T2"
    assert ranked[2].name == "T3"
    assert ranked[3].name == "T4"


def test_league_round_schemas():
    round_id = uuid.uuid4()
    league_id = uuid.uuid4()

    round_model = LeagueRound(
        id=round_id,
        league_id=league_id,
        round_number=1,
        name="Jornada 1",
        phase=1,
        start_date=date(2026, 10, 20),
        end_date=date(2026, 10, 27),
        extension_days=2,
    )

    resp = LeagueRoundResponse.model_validate(round_model)
    assert resp.id == round_id
    assert resp.name == "Jornada 1"
    assert resp.extension_days == 2

    # Update schema validation
    update_data = LeagueRoundUpdate(name="Jornada 1 - Modificada", extension_days=5)
    assert update_data.name == "Jornada 1 - Modificada"
    assert update_data.extension_days == 5
    assert update_data.start_date is None

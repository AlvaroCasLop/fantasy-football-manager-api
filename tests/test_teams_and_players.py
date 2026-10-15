import uuid
from src.app.models.player import Player
from src.app.models.team import Team
from src.app.modules.players.schemas import (
    PlayerAdvancement,
    PlayerCreate,
    PlayerResponse,
    PlayerUpdate,
)
from src.app.modules.teams.schemas import (
    TeamCreate,
    TeamDetailResponse,
    TeamResponse,
    TeamUpdate,
)


def test_team_create_and_response_schema():
    team_in = TeamCreate(
        name="Reikland Reavers",
        race="Human",
        treasury=1000000,
        rerolls=3,
        dedicated_fans=2,
    )
    assert team_in.name == "Reikland Reavers"
    assert team_in.rerolls == 3

    # Test from_attributes with an actual SQLAlchemy Team model instance
    team_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    team_model = Team(
        id=team_id,
        owner_id=owner_id,
        name="Reikland Reavers",
        race="Human",
        treasury=1000000,
        team_value=1000000,
        rerolls=3,
        assistant_coaches=1,
        cheerleaders=1,
        apothecary=True,
        dedicated_fans=2,
        roster_closed=False,
        wins=5,
        draws=1,
        losses=0,
        played=6,
        td_for=12,
        td_against=3,
        cas_for=8,
        cas_against=2,
        fouls_committed=1,
        inducements={},
        sprint_falls=0,
        dismissed_positionals=[],
    )

    team_res = TeamResponse.model_validate(team_model)
    assert team_res.id == team_id
    assert team_res.owner_id == owner_id
    assert team_res.apothecary is True
    assert team_res.wins == 5


def test_player_create_and_advancement_schema():
    team_id = uuid.uuid4()
    player_in = PlayerCreate(
        team_id=team_id,
        name="Griff Oberwald Jr",
        number=1,
        position="Blitzer",
        cost=90000,
        ma=7,
        st=3,
        ag="3+",
        pa="4+",
        av="8+",
        is_captain=True,
    )
    assert player_in.name == "Griff Oberwald Jr"
    assert player_in.is_captain is True

    # Test from_attributes with SQLAlchemy Player model instance
    player_id = uuid.uuid4()
    player_model = Player(
        id=player_id,
        team_id=team_id,
        name="Griff Oberwald Jr",
        number=1,
        position="Blitzer",
        cost=90000,
        ma=7,
        st=3,
        ag="3+",
        pa="4+",
        av="8+",
        spp=16,
        spp_spent=6,
        tv_added=20000,
        advancements=[{"type": "primary", "skill": "Dodge", "tvCost": 20000}],
        is_captain=True,
        sprint_falls=0,
        is_veteran=False,
    )

    player_res = PlayerResponse.model_validate(player_model)
    assert player_res.id == player_id
    assert player_res.spp == 16
    assert len(player_res.advancements) == 1
    assert player_res.is_captain is True


def test_team_detail_response_with_players():
    team_id = uuid.uuid4()
    team_model = Team(
        id=team_id,
        name="Skaven Blight",
        race="Skaven",
        treasury=850000,
        team_value=950000,
        rerolls=2,
        assistant_coaches=0,
        cheerleaders=0,
        apothecary=False,
        dedicated_fans=1,
        roster_closed=False,
        wins=0,
        draws=0,
        losses=0,
        played=0,
        td_for=0,
        td_against=0,
        cas_for=0,
        cas_against=0,
        fouls_committed=0,
        inducements={},
        sprint_falls=0,
        dismissed_positionals=[],
        players=[
            Player(
                id=uuid.uuid4(),
                team_id=team_id,
                name="Gutter Runner 1",
                number=7,
                position="Gutter Runner",
                cost=85000,
                ma=9,
                st=2,
                ag="2+",
                pa="4+",
                av="7+",
                spp=0,
            )
        ],
    )

    detail_res = TeamDetailResponse.model_validate(team_model)
    assert detail_res.id == team_id
    assert len(detail_res.players) == 1
    assert detail_res.players[0].name == "Gutter Runner 1"
    assert detail_res.players[0].ma == 9


def test_reference_data_elite_skills():
    from src.app.modules.reference_data.service import reference_data_service

    # Check both by slug ID and by display name
    assert reference_data_service.is_elite_skill("block") is True
    assert reference_data_service.is_elite_skill("Block") is True
    assert reference_data_service.is_elite_skill("dodge") is True
    assert reference_data_service.is_elite_skill("Dodge") is True
    assert reference_data_service.is_elite_skill("guard") is True
    assert reference_data_service.is_elite_skill("mighty-blow-1") is True
    assert reference_data_service.is_elite_skill("Mighty Blow (+1)") is True
    assert reference_data_service.is_elite_skill("frenzy") is False
    assert reference_data_service.is_elite_skill(None) is False

    assert "block" in reference_data_service.get_elite_skills()
    assert reference_data_service.get_skill("block")["name"] == "Block"
    assert reference_data_service.get_skill("Block")["id"] == "block"

    # Test race lookup and canonical positional skills (Option 1)
    skaven = reference_data_service.get_race("Skaven")
    assert skaven is not None
    assert "positionals" in skaven
    gutter_runner = next(p for p in skaven["positionals"] if p["title"] == "Gutter Runner")
    assert "dodge" in gutter_runner["skills"]  # canonical slug ID

    # Test star player lookup and canonical star skills (Option 1)
    akhorne = reference_data_service.get_star("akhorne")
    assert akhorne is not None
    assert "dodge" in akhorne["skills"]
    assert "claws" in akhorne["skills"]

    # Test skill resolution
    resolved = reference_data_service.resolve_skills(["dodge", "block"])
    assert len(resolved) == 2
    assert resolved[0]["name"] == "Dodge"
    assert resolved[1]["name"] == "Block"
    assert resolved[0]["is_elite"] is True


def test_calculate_advancement_costs_automatic():
    from src.app.modules.players.schemas import PlayerAdvancement
    from src.app.modules.players.service import player_service

    player = Player(
        id=uuid.uuid4(),
        name="Test Player",
        number=1,
        position="Lineman",
        cost=50000,
        spp=30,
        spp_spent=0,
        tv_added=0,
        advancements=[],
    )

    # 1st advancement (0 existing):
    # Non-elite primary: 20k TV, 6 SPP
    adv1 = PlayerAdvancement(type="primary", skill="tackle")
    tv, spp = player_service.calculate_advancement_costs(player, adv1)
    assert tv == 20000
    assert spp == 6

    # Elite primary (Block): 30k TV, 6 SPP
    adv_elite = PlayerAdvancement(type="primary", skill="block")
    tv_e, spp_e = player_service.calculate_advancement_costs(player, adv_elite)
    assert tv_e == 30000
    assert spp_e == 6

    # Secondary: 40k TV, 12 SPP
    adv_sec = PlayerAdvancement(type="secondary", skill="pass")
    tv_s, spp_s = player_service.calculate_advancement_costs(player, adv_sec)
    assert tv_s == 40000
    assert spp_s == 12

    # Stat ST: 80k TV, 18 SPP
    adv_stat = PlayerAdvancement(type="stat", stat="ST")
    tv_st, spp_st = player_service.calculate_advancement_costs(player, adv_stat)
    assert tv_st == 80000
    assert spp_st == 18

    # 2nd advancement (1 existing):
    player.advancements = [{"type": "primary", "skill": "tackle", "tv_cost": 20000, "spp_cost": 6}]
    # 2nd primary: 20k TV, 8 SPP
    adv2 = PlayerAdvancement(type="primary", skill="frenzy")
    tv2, spp2 = player_service.calculate_advancement_costs(player, adv2)
    assert tv2 == 20000
    assert spp2 == 8

    # 3rd advancement (2 existing):
    player.advancements.append({"type": "primary", "skill": "frenzy", "tv_cost": 20000, "spp_cost": 8})
    # 3rd primary: 20k TV, 12 SPP
    adv3 = PlayerAdvancement(type="primary", skill="sure-hands")
    tv3, spp3 = player_service.calculate_advancement_costs(player, adv3)
    assert tv3 == 20000
    assert spp3 == 12

    # Manual override test (e.g. tournament free skill)
    adv_override = PlayerAdvancement(type="primary", skill="block", tv_cost=0, spp_cost=0)
    tv_ov, spp_ov = player_service.calculate_advancement_costs(player, adv_override)
    assert tv_ov == 0
    assert spp_ov == 0


def test_league_schemas_and_invite_code():
    from src.app.models.league import League
    from src.app.modules.leagues.schemas import LeagueCreate, LeagueDetailResponse, LeagueResponse
    from src.app.modules.leagues.service import generate_invite_code

    # Test invite code format
    code = generate_invite_code()
    assert code.startswith("BB-")
    assert len(code) == 9  # "BB-" + 6 chars

    # Test LeagueCreate validation
    league_in = LeagueCreate(
        name="Liga de Verano BB2025",
        description="Torneo oficial",
        format="standard",
        game_mode="standard",
        is_double_round=False,
        is_public=True,
    )
    assert league_in.name == "Liga de Verano BB2025"
    assert league_in.is_double_round is False

    # Test LeagueResponse model validation
    league_id = uuid.uuid4()
    creator_id = uuid.uuid4()
    league_model = League(
        id=league_id,
        name="Liga de Verano BB2025",
        description="Torneo oficial",
        creator_id=creator_id,
        invite_code=code,
        format="standard",
        game_mode="standard",
        is_double_round=False,
        is_public=True,
        status="draft",
        current_phase=1,
        commissioner_ids=[creator_id],
    )

    res = LeagueResponse.model_validate(league_model)
    assert res.id == league_id
    assert res.name == "Liga de Verano BB2025"
    assert res.invite_code == code
    assert res.status == "draft"
    assert res.commissioner_ids == [creator_id]

    detail = LeagueDetailResponse.model_validate(league_model)
    assert detail.id == league_id
    assert len(detail.teams) == 0






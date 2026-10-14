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

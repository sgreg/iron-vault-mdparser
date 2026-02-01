from utils import (
    ParserArgsData,
    ParserData,
    assert_parser_args,
    assert_parser_data,
    element_text,
)

from ironvaultmd.parsers.nodes import (
    AddNodeParser,
    BurnNodeParser,
    ClockNodeParser,
    ImpactNodeParser,
    InitiativeNodeParser,
    MeterNodeParser,
    MoveNodeParser,
    OocNodeParser,
    OracleNodeParser,
    PositionNodeParser,
    ProgressNodeParser,
    ProgressRollNodeParser,
    RerollNodeParser,
    RollNodeParser,
    RollsNodeParser,
    TrackNodeParser,
    XpNodeParser,
)


def test_parser_add(ctx):
    parser = AddNodeParser()

    assert parser.names.name == "Add"
    assert parser.input_regex
    assert not parser.extra_regex

    classes = ["add"]

    rolls = [
        ParserData("2", True, 0, classes),
        ParserData('2 "comment"', True, 1, classes),
        ParserData('2 "longer comment with *all* _kinds_ ~of~ **stuff** in it"', True, 2, classes),
        ParserData("-2", False),
        ParserData("", False),
        ParserData("random data", False),
    ]

    # FIXME this tests the classes and with that somewhat the parsers, but should compare HTML output as well
    nodes = assert_parser_data(parser, ctx, rolls, classes)
    assert "comment" in element_text(nodes[1])


def test_parser_add_args(ctx):
    data = [
        ParserArgsData("1", {"add": 1, "reason": None}),
        ParserArgsData('1 "because"', {"add": 1, "reason": "because"}),
        ParserArgsData('1 "because reasons"', {"add": 1, "reason": "because reasons"}),
    ]

    assert_parser_args(AddNodeParser(), ctx, data)


def test_parser_burn(block_ctx):
    parser = BurnNodeParser()

    assert parser.names.name == "Burn"
    assert parser.input_regex
    assert not parser.extra_regex

    classes = ["meter-burn"]

    rolls = [
        ParserData("from=8 to=2", True, 0, classes),
        ParserData("from=2 to=8", True, 1, classes), # makes no sense, but still valid for parsing
        ParserData("to=2", False),
        ParserData("from=8", False),
        ParserData("from=text to=2", False),
        ParserData("from=8 to=text", False),
        ParserData("from=-1 to=2", False),
        ParserData("from=8 to=-1", False),
        ParserData("", False),
        ParserData("random data", False),
    ]

    assert_parser_data(parser, block_ctx, rolls, classes)


def test_parser_burn_args(block_ctx):
    data = [
        ParserArgsData("from=4 to=2", {"from": 4, "to": 2, "stat_name": "", "score": 4, "vs1": 0, "vs2": 0, "hitmiss": "strong", "match": True}),
    ]

    assert_parser_args(BurnNodeParser(), block_ctx, data)


def test_parser_clock(ctx):
    parser = ClockNodeParser()

    assert parser.names.name == "Clock"
    assert parser.input_regex
    assert parser.extra_regex

    classes = ["clock"]

    rolls = [
        ParserData('from=2 name="[[ignored|Clock Name]]" out-of=6 to=3', True, 0, classes),
        # allow all kinds of ranks and steps even though they make no sense in practice
        ParserData('from=2 name="[[ignored|Clock Name]]" out-of=6 to=100', True, 1, classes),
        ParserData('from=2 name="[[ignored|Clock Name]]" out-of=1 to=3', True, 2, classes),
        ParserData('from=100 name="[[ignored|Clock Name]]" out-of=6 to=3', True, 3, classes),
        # allow valid status changes (added, removed, resolved)
        ParserData('name="[[ignored|Clock Name]]" status="added"', True, 4, classes),
        ParserData('name="[[ignored|Clock Name]]" status="removed"', True, 5, classes),
        ParserData('name="[[ignored|Clock Name]]" status="resolved"', True, 6, classes),
        # FIXME revisit these, using parameter parser makes these succeed now
        # ParserData('from=2 name="[[ignored]]" out-of=6 to=3', False),
        # ParserData('name="[[ignored|Clock Name]]" out-of=6 to=3', False),
        # ParserData('from=2 out-of=6 to=3', False),
        # ParserData('from=2 name="[[ignored|Clock Name]]" to=3', False),
        # ParserData('from=2 name="[[ignored|Clock Name]]" out-of=6', False),
        # ParserData('name="[[ignored|Clock Name]]" status="invalid"', False),
        # ParserData('name="[[ignored|Clock Name]]" status="added" out-of=6 to=3', False),
        ParserData("", False),
        ParserData("random data", False),
    ]

    nodes = assert_parser_data(parser, ctx, rolls, classes)
    assert "Clock Name" in element_text(nodes[0])


def test_parser_clock_args(ctx):
    data = [
        ParserArgsData('name="a clock" from=3 to=4 out-of=6', {"name": "a clock", "from": 3, "to": 4, "segments": 6, "extra": {}}),
        ParserArgsData('to=4 out-of=6 name="a clock" from=3', {"name": "a clock", "from": 3, "to": 4, "segments": 6, "extra": {}}),
        ParserArgsData('from=2 to=4 out-of=4', {"name": "unknown", "from": 2, "to": 4, "segments": 4, "extra": {}}),
        ParserArgsData('name="another clock" status="added"', {"name": "another clock", "status": "added", "extra": {}}),
        ParserArgsData('status="removed"', {"name": "unknown", "status": "removed", "extra": {}}),
        ParserArgsData('status="removed" unexpected="value"', {"name": "unknown", "status": "removed", "extra": {"unexpected": "value"}}),
    ]

    assert_parser_args(ClockNodeParser(), ctx, data)


def test_parser_impact(ctx):
    parser = ImpactNodeParser()

    assert parser.names.name == "Impact"
    assert parser.input_regex
    assert not parser.extra_regex

    classes = [
        "impact",
        "impact-marked",
        "impact-unmarked",
    ]

    data = [
        ParserData('"Wounded" true', True, 0, ["impact", "impact-marked"]),
        ParserData('"Wounded" false', True, 1, ["impact", "impact-cleared"]),
        ParserData('"Permanently Harmed" true', True, 2, ["impact", "impact-marked"]),
        ParserData('"Permanently Harmed" false', True, 3, ["impact", "impact-cleared"]),
        ParserData('"some random something" true', True, 4, ["impact", "impact-marked"]),
        ParserData('"Wounded" unknown', False),
        ParserData('"Wounded"', False),
        ParserData('Wounded false', False)
    ]

    assert_parser_data(parser, ctx, data, classes)


def test_parser_impact_args(ctx):
    data = [
        ParserArgsData('"Wounded" true', {"impact": "Wounded", "marked": True}),
        ParserArgsData('"wounded" true', {"impact": "wounded", "marked": True}),
        ParserArgsData('"Naked and Afraid" false', {"impact": "Naked and Afraid", "marked": False}),
    ]

    assert_parser_args(ImpactNodeParser(), ctx, data)


def test_parser_initiative(ctx):
    parser = InitiativeNodeParser()

    assert parser.names.name == "Initiative"
    assert parser.input_regex
    assert not parser.extra_regex

    classes = [
        "initiative-nocombat",
        "initiative-initiative",
        "initiative-noinitiative",
    ]

    rolls = [
        ParserData('from="out of combat" to="has initiative"', True, 0, ["initiative-initiative"]),
        ParserData('from="out of combat" to="no initiative"', True, 1, ["initiative-noinitiative"]),
        ParserData('from="no initiative" to="has initiative"', True, 2, ["initiative-initiative"]),
        ParserData('from="no initiative" to="out of combat"', True, 3, ["initiative-nocombat"]),
        ParserData('from="has initiative" to="no initiative"', True, 4, ["initiative-noinitiative"]),
        ParserData('from="has initiative" to="out of combat"', True, 5, ["initiative-nocombat"]),
        ParserData('from="out of combat" to="out of combat"', True, 6, ["initiative-nocombat"]),
        ParserData('from="has initiative" to="has initiative"', True, 7, ["initiative-initiative"]),
        ParserData('from="no initiative" to="no initiative"', True, 8, ["initiative-noinitiative"]),
        ParserData('from="out of combat" to="unknown"', True, 9, []),
        ParserData('from="has initiative" to="unknown"', True, 10, []),
        ParserData('from="no initiative" to="unknown"', True, 11, []),
        ParserData('from=out of combat to="unknown"', False),
        ParserData('from="out of combat" to=has initiative', False),
        ParserData(' to="has initiative"', False),
        ParserData('from="out of combat"', False),
        ParserData("", False),
        ParserData("random data", False),
    ]

    assert_parser_data(parser, ctx, rolls, classes)


def test_parser_initiative_args(ctx):
    data = [
        ParserArgsData('from="out of combat" to="has initiative"', {"from": "out of combat", "to": "has initiative", "from_slug": "nocombat", "to_slug": "initiative"}),
        ParserArgsData('from="has initiative" to="no initiative"', {"from": "has initiative", "to": "no initiative", "from_slug": "initiative", "to_slug": "noinitiative"}),
    ]

    assert_parser_args(InitiativeNodeParser(), ctx, data)


def test_parser_meter(ctx):
    parser = MeterNodeParser()

    assert parser.names.name == "Meter"
    assert parser.input_regex
    assert not parser.extra_regex

    classes = [
        "meter-increase",
        "meter-decrease",
    ]

    rolls = [
        ParserData('"Momentum" from=5 to=6', True, 0, ["meter-increase"]),
        ParserData('"Momentum" from=6 to=5', True, 1, ["meter-decrease"]),
        ParserData('"Momentum" from=6 to=6', True, 2, ["meter-increase"]),
        ParserData('"!@#$%^&*()" from=5 to=6', True, 3, ["meter-increase"]),
        ParserData('"Multi-word meter \\/ name" from=6 to=5', True, 4, ["meter-decrease"]),
        ParserData('"[[Linked meter|Meter with Link]]" from=5 to=6', True, 5, ["meter-increase"]),
        ParserData('Momentum from=6 to=6', False),
        ParserData('"" from=5 to=6', False),
        ParserData('from=5 to=6', False),
        ParserData('"Momentum" to=6', False),
        ParserData('"Momentum" from=5', False),
        ParserData('"Momentum" from=text to=6', False),
        ParserData('"Momentum" from=5 to=text', False),
        ParserData('"Momentum" from=-1 to=6', False),
        ParserData('"Momentum" from=5 to=-1', False),
        ParserData("", False),
        ParserData("random data", False),
    ]

    nodes = assert_parser_data(parser, ctx, rolls, classes)
    assert "Momentum" in element_text(nodes[0])
    assert "!@#$%^&*()" in element_text(nodes[3])
    assert "Multi-word meter / name" in element_text(nodes[4])
    assert "Meter with Link" in element_text(nodes[5])


def test_parser_meter_args(ctx):
    data = [
        ParserArgsData('"Health" from=4 to=3', {"meter_name": "Health", "from": 4, "to": 3, "diff": -1}),
        ParserArgsData('"Starship \\/ Integrity" from=2 to=3', {"meter_name": "Starship / Integrity", "from": 2, "to": 3, "diff": 1}),
    ]

    assert_parser_args(MeterNodeParser(), ctx, data)


def test_parser_move(ctx):
    parser = MoveNodeParser()

    assert parser.names.name == "Move"
    assert parser.input_regex
    assert not parser.extra_regex

    classes = ["move"]

    rolls = [
        ParserData('"[Move Name](datasworn:path)"', True, 0, classes),
        ParserData('[Move Name](datasworn:path)', False),
        ParserData(' "[Move Name](datasworn:path)"', False),
        ParserData('[Move Name](datasworn:path) ', False),
        ParserData("Move Name", False),
    ]

    nodes = assert_parser_data(parser, ctx, rolls, classes)
    move_name = nodes[0].findall('div')
    assert move_name is not None
    assert "Move Name" in move_name[0].text


def test_parser_move_args(ctx):
    data = [
        ParserArgsData('"[Compel](datasworn:move:starforged\\/adventure\\/compel)"', {"name": "Compel"}),
        ParserArgsData('"[Secure an Advantage](datasworn:move:starforged\\/adventure\\/secure_an_advantage)"', {"name": "Secure an Advantage"}),
    ]

    assert_parser_args(MoveNodeParser(), ctx, data)


def test_parser_ooc(ctx):
    parser = OocNodeParser()

    assert parser.names.name == "OOC"
    assert parser.input_regex
    assert not parser.extra_regex

    assert ctx.parent.find("div") is None

    contents = [
        "ooc",
        "anything really=goes from=3 to **markdown** _content_ ~and~ *everything*",
        "escaped \"quoted\" text too",
        'unescaped "quoted" text too, even though that is not possible from iron-vault itself',
    ]

    for content in contents:
        parser.parse(ctx, f'"{content}"')

    nodes = ctx.parent.findall("div")
    assert len(nodes) == len(contents)
    for idx, node in enumerate(nodes):
        assert node.get("class") == "ivm-ooc"
        assert contents[idx] in node.text


def test_parser_ooc_args(ctx):
    data = [
        ParserArgsData('"comment"', {"comment": "comment"}),
        ParserArgsData('"several words comment"', {"comment": "several words comment"}),
        ParserArgsData('"comment with \\"quoted\\" text"', {"comment": 'comment with "quoted" text'}),
    ]

    assert_parser_args(OocNodeParser(), ctx, data)


def test_parser_oracle(ctx):
    parser = OracleNodeParser()

    assert parser.names.name == "Oracle"
    assert parser.input_regex
    assert parser.extra_regex

    classes = ["oracle"]

    rolls = [
        ParserData('name="[Oracle Name](datasworn:path)" result="Something" roll=55', True, 0, classes),
        ParserData('name="[Oracle Name]" result="Something" roll=55', True, 1, classes),
        ParserData('name="something with just a name" result="Something" roll=55', True, 2, classes),
        # FIXME revisit these, using parameter parser makes these succeed now
        # ParserData('name="" result="Something" roll=55', False),
        # ParserData('result="Something" roll=55', False),
        # ParserData('name="[Oracle Name](datasworn:path)" result=Something roll=55', False),
        # ParserData('name="[Oracle Name](datasworn:path)" roll=55', False),
        # ParserData('name="[Oracle Name](datasworn:path)" result="Something" roll=text', False),
        # ParserData('name="[Oracle Name](datasworn:path)" result="Something" roll=-1', False),
        # ParserData('name="[Oracle Name](datasworn:path)" result="Something"', False),
        ParserData("", False),
        ParserData("random data", False),
    ]

    nodes = assert_parser_data(parser, ctx, rolls, classes)
    assert "Oracle Name" in element_text(nodes[0])
    assert "Something" in element_text(nodes[0])


def test_parser_oracle_args(ctx):
    data = [
        ParserArgsData('name="[Core Oracles \\/ Theme](datasworn:path)" result="Warning" roll=96', {"oracle": "Core Oracles / Theme", "result": "Warning", "roll": 96, "extra": {}}),
        ParserArgsData("roll=12", {"oracle": "unknown", "result": "unknown", "roll": 12, "extra": {}}),
        ParserArgsData('cursed=1 name="something" replaced=true result="Pyramid architecture" roll=74', {"oracle": "something", "result": "Pyramid architecture", "roll": 74, "cursed": 1, "replaced": True, "extra": {}}),
        ParserArgsData("roll=12 random=3", {"oracle": "unknown", "result": "unknown", "roll": 12, "extra": {"random": 3}}),
    ]

    assert_parser_args(OracleNodeParser(), ctx, data)


def test_parser_position(ctx):
    parser = PositionNodeParser()

    assert parser.names.name == "Position"
    assert parser.input_regex
    assert not parser.extra_regex

    classes = [
        "position-nocombat",
        "position-control",
        "position-badspot",
    ]

    rolls = [
        ParserData('from="out of combat" to="in control"', True, 0, ["position-control"]),
        ParserData('from="out of combat" to="in a bad spot"', True, 1, ["position-badspot"]),
        ParserData('from="in a bad spot" to="in control"', True, 2, ["position-control"]),
        ParserData('from="in a bad spot" to="out of combat"', True, 3, ["position-nocombat"]),
        ParserData('from="in control" to="in a bad spot"', True, 4, ["position-badspot"]),
        ParserData('from="in control" to="out of combat"', True, 5, ["position-nocombat"]),
        ParserData('from="out of combat" to="out of combat"', True, 6, ["position-nocombat"]),
        ParserData('from="in control" to="in control"', True, 7, ["position-control"]),
        ParserData('from="in a bad spot" to="in a bad spot"', True, 8, ["position-badspot"]),
        ParserData('from="out of combat" to="unknown"', True, 9, []),
        ParserData('from="in control" to="unknown"', True, 10, []),
        ParserData('from="in a bad spot" to="unknown"', True, 11, []),
        ParserData('from=out of combat to="unknown"', False),
        ParserData('from="out of combat" to=in control', False),
        ParserData(' to="in control"', False),
        ParserData('from="out of combat"', False),
        ParserData("", False),
        ParserData("random data", False),
    ]

    assert_parser_data(parser, ctx, rolls, classes)


def test_parser_position_args(ctx):
    data = [
        ParserArgsData('from="out of combat" to="in control"', {"from": "out of combat", "to": "in control", "from_slug": "nocombat", "to_slug": "control"}),
        ParserArgsData('from="in control" to="in a bad spot"', {"from": "in control", "to": "in a bad spot", "from_slug": "control", "to_slug": "badspot"}),
    ]

    assert_parser_args(PositionNodeParser(), ctx, data)


def test_parser_progress(ctx):
    parser = ProgressNodeParser()

    assert parser.names.name == "Progress"
    assert parser.input_regex
    assert parser.extra_regex

    classes = ["progress"]

    rolls = [
        ParserData('from=6 name="[[ignored|Track Name]]" rank="dangerous" steps=1', True, 0, classes),
        # allow all kinds of ranks and steps even though they make no sense in practice
        ParserData('from=6 name="[[ignored|Track Name]]" rank="dangerous" steps=100', True, 1, classes),
        ParserData('from=6 name="[[ignored|Track Name]]" rank="unknown" steps=1', True, 2, classes),
        ParserData('from=100 name="[[ignored|Track Name]]" rank="dangerous" steps=1', True, 3, classes),
        # don't allow all else
        # FIXME revisit these, using parameter parser makes these succeed now
        # ParserData('from=6 name="" rank="dangerous" steps=1', False),
        # ParserData('from=6 name="[[ignored]]" rank="dangerous" steps=1', False),
        # ParserData('name="[[ignored|Track Name]]" rank="dangerous" steps=1', False),
        # ParserData('from=6 rank="dangerous" steps=1', False),
        # ParserData('from=6 name="[[ignored|Track Name]]" steps=1', False),
        # ParserData('from=6 name="[[ignored|Track Name]]" rank="dangerous"', False),
        ParserData("", False),
        ParserData("random data", False),
    ]

    nodes = assert_parser_data(parser, ctx, rolls, classes)

    assert "Track Name" in element_text(nodes[0])


def test_parser_progress_args(ctx):
    data = [
        ParserArgsData('from=8 name="track" rank="dangerous" steps=1', {"name": "track", "rank": "dangerous", "steps": 1, "from": (2, 0), "to": (4, 0), "from_ticks": 8, "to_ticks": 16, "from_fract": 2.0, "to_fract": 4.0, "ticks": 8, "extra": {}}),
        ParserArgsData('from=8 name="track" rank="dangerous" steps=1 else="something"', {"name": "track", "rank": "dangerous", "steps": 1, "from": (2, 0), "to": (4, 0), "from_ticks": 8, "to_ticks": 16, "from_fract": 2.0, "to_fract": 4.0, "ticks": 8, "extra": {"else": "something"}}),
    ]

    assert_parser_args(ProgressNodeParser(), ctx, data)


def test_parser_progressroll(block_ctx):
    parser = ProgressRollNodeParser()

    assert parser.names.name == "Progress Roll"
    assert parser.input_regex
    assert parser.extra_regex

    classes = [
        "roll-strong",
        "roll-weak",
        "roll-miss",
        "roll-match",
    ]

    rolls = [
        ParserData('name="[[ignored|Track Name]]" score=6 vs1=3 vs2=5', True, 0, ["roll-strong"]),
        ParserData('name="[[ignored|Track Name]]" score=6 vs1=3 vs2=6', True, 1, ["roll-weak"]),
        ParserData('name="[[ignored|Track Name]]" score=6 vs1=3 vs2=7', True, 2, ["roll-weak"]),
        ParserData('name="[[ignored|Track Name]]" score=6 vs1=6 vs2=7', True, 3, ["roll-miss"]),
        ParserData('name="[[ignored|Track Name]]" score=6 vs1=6 vs2=6', True, 4, ["roll-miss", "roll-match"]),
        ParserData('name="[[ignored|Track Name]]" score=6 vs1=3 vs2=3', True, 5, ["roll-strong", "roll-match"]),
        ParserData('score=6 vs1=3 vs2=5', True, 6, ["roll-strong"]),
        ParserData('score=6 vs1=3 vs2=5 name="[[ignored|Name in the back]]"', True, 7, ["roll-strong"]),
        # FIXME revisit these, using parameter parser makes these succeed now
        # ParserData('name="" score=6 vs1=3 vs2=5', False),
        # ParserData('name="[[ignored]]" score=6 vs1=3 vs2=5', False),
        # ParserData('score=text vs1=3 vs2=5', False),
        # ParserData('score=6 vs1=text vs2=5', False),
        # ParserData('score=6 vs1=3 vs2=text', False),
        # ParserData('score=-1 vs1=3 vs2=5', False),
        # ParserData('score=6 vs1=-1 vs2=5', False),
        # ParserData('score=6 vs1=3 vs2=-1', False),
        # ParserData(' vs1=3 vs2=5', False),
        # ParserData('score=6 vs2=5', False),
        # ParserData('score=6 vs1=3', False),
        ParserData("", False),
        ParserData("random data", False)
    ]

    nodes = assert_parser_data(parser, block_ctx, rolls, classes)

    assert "Track Name" in element_text(nodes[0])
    assert "undefined" in element_text(nodes[6])
    assert "Name in the back" in element_text(nodes[7])


def test_parser_progressroll_args(block_ctx):
    data = [
        ParserArgsData('name="track" score=8 vs1=4 vs2=10', {"name": "track", "score": 8, "vs1": 4, "vs2": 10, "stat_name": "", "hitmiss": "weak", "match": False, "extra": {}}),
        ParserArgsData("score=8 vs1=4 vs2=10", {"name": "undefined", "score": 8, "vs1": 4, "vs2": 10, "stat_name": "", "hitmiss": "weak", "match": False, "extra": {}}),
        ParserArgsData('score=8 vs1=4 vs2=10 track="name"', {"name": "undefined", "score": 8, "vs1": 4, "vs2": 10, "stat_name": "", "hitmiss": "weak", "match": False, "extra": {"track": "name"}}),
    ]

    assert_parser_args(ProgressRollNodeParser(), block_ctx, data)


def test_parser_reroll(block_ctx):
    parser = RerollNodeParser()

    assert parser.names.name == "Reroll"
    assert parser.input_regex
    assert not parser.extra_regex

    classes = ["reroll"]

    rolls = [
        ParserData('action="1"', True, 0, classes),
        ParserData('vs1="2"', True, 1, classes),
        ParserData('vs2="3"', True, 2, classes),
        # invalid values from d6 / d10 point of view, but there's no check for that, so expect success
        ParserData('action="0"', True, 3, classes),
        ParserData('action="10"', True, 4, classes),
        ParserData('vs1="0"', True, 5, classes),
        ParserData('vs1="11"', True, 6, classes),
        ParserData('vs2="0"', True, 7, classes),
        ParserData('vs2="11"', True, 8, classes),
        # actual invalid, and expected as such
        ParserData('action="text"', False),
        ParserData('vs1="text"', False),
        ParserData('vs2="text"', False),
        ParserData('action="-1"', False),
        ParserData('vs1="-1"', False),
        ParserData('vs2="-1"', False),
        ParserData('vs3="5"', False),
        ParserData('adds="5"', False),
        ParserData('""="5"', False),
        ParserData('"action"=""', False),
        ParserData("", False),
        ParserData("random data", False),
    ]

    assert_parser_data(parser, block_ctx, rolls, classes)


def test_parser_reroll_args(block_ctx):
    data = [
        ParserArgsData('action="5"', {"die": "action", "value": 5, "old_value": 0, "stat_name": "", "score": 5, "vs1": 0, "vs2": 0, "hitmiss": "strong", "match": True}),
        ParserArgsData('vs1="8"', {"die": "vs1", "value": 8, "old_value": 0, "stat_name": "", "score": 5, "vs1": 8, "vs2": 0, "hitmiss": "weak", "match": False}),
        ParserArgsData('vs2="6"', {"die": "vs2", "value": 6, "old_value": 0, "stat_name": "", "score": 5, "vs1": 8, "vs2": 6, "hitmiss": "miss", "match": False}),
        ParserArgsData('vs1="6"', {"die": "vs1", "value": 6, "old_value": 8, "stat_name": "", "score": 5, "vs1": 6, "vs2": 6, "hitmiss": "miss", "match": True}),
    ]

    assert_parser_args(RerollNodeParser(), block_ctx, data)


def test_parser_roll(block_ctx):
    parser = RollNodeParser()

    assert parser.names.name == "Roll"
    assert parser.input_regex
    assert not parser.extra_regex

    classes = [
        "roll-strong",
        "roll-weak",
        "roll-miss",
        "roll-match",
    ]

    rolls = [
        ParserData('"wits" action=4 adds=0 stat=2 vs1=3 vs2=4', True, 0, ["roll-strong"]),
        ParserData('"wits" action=4 adds=0 stat=2 vs1=3 vs2=6', True, 1, ["roll-weak"]),
        ParserData('"wits" action=4 adds=1 stat=2 vs1=3 vs2=6', True, 2, ["roll-strong"]),
        ParserData('"wits" action=2 adds=0 stat=2 vs1=7 vs2=6', True, 3, ["roll-miss"]),
        ParserData('"wits" action=4 adds=1 stat=2 vs1=3 vs2=3', True, 4, ["roll-strong", "roll-match"]),
        ParserData('"wits" action=2 adds=0 stat=2 vs1=7 vs2=7', True, 5, ["roll-miss", "roll-match"]),
        ParserData('wits action=2 adds=0 stat=2 vs1=7 vs2=7', False),
        ParserData('"" action=2 adds=0 stat=2 vs1=7 vs2=7', False),
        ParserData('"wits" action=text adds=0 stat=2 vs1=7 vs2=7', False),
        ParserData('"wits" action=2 adds=text stat=2 vs1=7 vs2=7', False),
        ParserData('"wits" action=2 adds=0 stat=text vs1=7 vs2=7', False),
        ParserData('"wits" action=2 adds=0 stat=2 vs1=text vs2=7', False),
        ParserData('"wits" action=2 adds=0 stat=2 vs1=7 vs2=text', False),
        ParserData('"wits" action=-1 adds=0 stat=2 vs1=7 vs2=7', False),
        ParserData('"wits" action=4 adds=-1 stat=2 vs1=7 vs2=7', False),
        ParserData('"wits" action=4 adds=0 stat=-1 vs1=7 vs2=7', False),
        ParserData('"wits" action=4 adds=0 stat=2 vs1=-1 vs2=7', False),
        ParserData('"wits" action=4 adds=0 stat=2 vs1=7 vs2=-1', False),
        ParserData('"wits" adds=0 stat=2 vs1=7 vs2=7', False),
        ParserData('"wits" action=2 stat=2 vs1=7 vs2=7', False),
        ParserData('"wits" action=2 adds=0 vs1=7 vs2=7', False),
        ParserData('"wits" action=2 adds=0 stat=2 vs2=7', False),
        ParserData('"wits" action=2 adds=0 stat=2 vs1=7', False),
        ParserData("", False),
        ParserData('random data', False),
    ]

    assert_parser_data(parser, block_ctx, rolls, classes)


def test_parser_roll_args(block_ctx):
    data = [
        ParserArgsData('"Heart" action=5 adds=0 stat=2 vs1=4 vs2=8', {"stat_name": "Heart", "action": 5, "adds": 0, "stat": 2, "score": 7, "vs1": 4, "vs2": 8, "hitmiss": "weak", "match": False}),
        ParserArgsData('"Edge" action=3 adds=1 stat=3 vs1=5 vs2=5', {"stat_name": "Edge", "action": 3, "adds": 1, "stat": 3, "score": 7, "vs1": 5, "vs2": 5, "hitmiss": "strong", "match": True}),
    ]

    assert_parser_args(RollNodeParser(), block_ctx, data)


def test_parser_rolls(block_ctx):
    parser = RollsNodeParser()

    assert parser.names.name == "Rolls"
    assert parser.input_regex
    assert not parser.extra_regex

    rolls = [
        ParserData('1 dice="1d10"', True, 0),
        ParserData('100 dice="1d100"', True, 1),
        ParserData('12 34 dice="2d100"', True, 2),
        ParserData('1 2 3 dice="3d6"', True, 3),
        ParserData('6 dice="invalid"', False),
        ParserData('4 dice="1D10"', False), # lowercase 'd' expected
        ParserData('dice="1d6" 1', False),
        ParserData("", False),
        ParserData('random data', False),
    ]

    nodes = assert_parser_data(parser, block_ctx, rolls, [])

    assert "12 34" in element_text(nodes[2])
    assert "2d100" in element_text(nodes[2])

def test_parser_rolls_args(ctx):
    data = [
        ParserArgsData('12 34 5 dice="3d100"', {"dice": "3d100", "rolls": "12 34 5", "rolls_array": [12, 34, 5]}),
        ParserArgsData('1 dice="1d6"', {"dice": "1d6", "rolls": "1", "rolls_array": [1]}),
    ]

    assert_parser_args(RollsNodeParser(), ctx, data)


def test_parser_track(ctx):
    parser = TrackNodeParser()

    assert parser.names.name == "Track"
    assert parser.input_regex
    assert parser.extra_regex

    classes = ["track"]

    rolls = [
        ParserData('name="[[ignored|Track Name]]" status="removed"', True, 0, classes),
        # FIXME revisit these, using parameter parser makes these succeed now
        # ParserData('name=[[ignored|Track Name]] status="removed"', False),
        # ParserData('name="[[ignored|Track Name]]" status=removed', False),
        # ParserData('name="" status="removed"', False),
        # ParserData('name="[[just a link without name]]" status="removed"', False),
        # ParserData('name="[[ignored|Track Name]]" status=""', False),
        # ParserData('status="removed"', False),
        # ParserData('name="[[ignored|Track Name]]"', False),
        ParserData("", False),
        ParserData("random data", False),
    ]

    nodes = assert_parser_data(parser, ctx, rolls, classes)
    assert "Track Name" in element_text(nodes[0])


def test_parser_track_args(ctx):
    data = [
        ParserArgsData('name="[[Campaign\\/Progress\\/Track.md|Track]]" status="added"', {"name": "Track", "status": "added", "extra": {}}),
        ParserArgsData('status="removed"', {"name": "undefined", "status": "removed", "extra": {}}),
        ParserArgsData('status="removed" unexpected="value"', {"name": "undefined", "status": "removed", "extra": {"unexpected": "value"}}),
        ParserArgsData('status="removed" expected=false', {"name": "undefined", "status": "removed", "extra": {"expected": False}}),
    ]

    assert_parser_args(TrackNodeParser(), ctx, data)


def test_parser_xp(ctx):
    parser = XpNodeParser()

    assert parser.names.name == "XP"
    assert parser.input_regex
    assert not parser.extra_regex

    classes = [
        "ivm-xp",
        "ivm-xp-inc",
        "ivm-xp-dec",
    ]

    rolls = [
        ParserData("from=2 to=4", True, 0, ["ivm-xp", "ivm-xp-inc"]),
        ParserData("from=6 to=2", True, 1, ["ivm-xp", "ivm-xp-dec"]),
        ParserData("from=2 to=2", True, 2, ["ivm-xp", "ivm-xp-inc"]), # pointless but still valid
        ParserData("to=2", False),
        ParserData("from=8", False),
        ParserData("from=text to=2", False),
        ParserData("from=8 to=text", False),
        ParserData("from=-1 to=2", False),
        ParserData("from=8 to=-1", False),
        ParserData("", False),
        ParserData("random data", False),
    ]

    assert_parser_data(parser, ctx, rolls, classes)


def test_parser_xp_args(ctx):
    data = [
        ParserArgsData("from=1 to=2", {"from": 1, "to": 2, "diff": 1}),
        ParserArgsData("from=6 to=4", {"from": 6, "to": 4, "diff": -2}),
    ]

    assert_parser_args(XpNodeParser(), ctx, data)

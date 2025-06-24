from utils import ParserData, assert_parser_data

from ironvaultmd.parsers.nodes import (
    AddNodeParser,
    BurnNodeParser,
    ClockNodeParser,
    MeterNodeParser,
    OocNodeParser,
    OracleNodeParser,
    PositionNodeParser,
    ProgressNodeParser,
    ProgressRollNodeParser,
    RerollNodeParser,
    RollNodeParser,
    TrackNodeParser,
)


def test_parser_add(parent):
    parser = AddNodeParser()

    assert parser.node_name == "Add"
    assert parser.regex

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
    nodes = assert_parser_data(parser, parent, rolls, classes)
    assert "comment" in nodes[1].text


def test_parser_burn(parent):
    parser = BurnNodeParser()

    assert parser.node_name == "Burn"
    assert parser.regex

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

    assert_parser_data(parser, parent, rolls, classes)


def test_parser_clock(parent):
    parser = ClockNodeParser()

    assert parser.node_name == "Clock"
    assert parser.regex

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
        # don't allow all else
        ParserData('from=2 name="" out-of=6 to=3', False),
        ParserData('from=2 name="[[ignored]]" out-of=6 to=3', False),
        ParserData('name="[[ignored|Clock Name]]" out-of=6 to=3', False),
        ParserData('from=2 out-of=6 to=3', False),
        ParserData('from=2 name="[[ignored|Clock Name]]" to=3', False),
        ParserData('from=2 name="[[ignored|Clock Name]]" out-of=6', False),
        ParserData('name="[[ignored|Clock Name]]" status="invalid"', False),
        ParserData('name="[[ignored|Clock Name]]" status="added" out-of=6 to=3', False),
        ParserData("", False),
        ParserData("random data", False),
    ]

    nodes = assert_parser_data(parser, parent, rolls, classes)
    assert "Clock Name" in nodes[0].text


def test_parser_meter(parent):
    parser = MeterNodeParser()

    assert parser.node_name == "Meter"
    assert parser.regex

    classes = [
        "meter-increase",
        "meter-decrease",
    ]

    rolls = [
        ParserData('"Momentum" from=5 to=6', True, 0, ["meter-increase"]),
        ParserData('"Momentum" from=6 to=5', True, 1, ["meter-decrease"]),
        ParserData('"Momentum" from=6 to=6', True, 2, []),
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

    nodes = assert_parser_data(parser, parent, rolls, classes)
    assert "Momentum" in nodes[0].text


def test_parser_ooc(parent):
    parser = OocNodeParser()

    assert parser.node_name == "OOC"
    assert parent.find("div") is None

    contents = [
        "",
        "ooc",
        "anything really=goes from=3 to **markdown** _content_ ~and~ *everything*"
    ]

    for content in contents:
        parser.parse(parent, content)

    nodes = parent.findall("div")
    assert len(nodes) == len(contents)
    for idx, node in enumerate(nodes):
        assert node.get("class") == "ivm-ooc"
        assert contents[idx] in node.text


def test_parser_oracle(parent):
    parser = OracleNodeParser()

    assert parser.node_name == "Oracle"
    assert parser.regex

    classes = ["oracle"]

    rolls = [
        ParserData('name="[Oracle Name](datasworn:path)" result="Something" roll=55', True, 0, classes),
        ParserData('name="[Oracle Name]" result="Something" roll=55', True, 1, classes),
        ParserData('name="something with just a name" result="Something" roll=55', True, 2, classes),
        ParserData('name="" result="Something" roll=55', False),
        ParserData('result="Something" roll=55', False),
        ParserData('name="[Oracle Name](datasworn:path)" result=Something roll=55', False),
        ParserData('name="[Oracle Name](datasworn:path)" roll=55', False),
        ParserData('name="[Oracle Name](datasworn:path)" result="Something" roll=text', False),
        ParserData('name="[Oracle Name](datasworn:path)" result="Something" roll=-1', False),
        ParserData('name="[Oracle Name](datasworn:path)" result="Something"', False),
        ParserData("", False),
        ParserData("random data", False),
    ]

    nodes = assert_parser_data(parser, parent, rolls, classes)
    assert "Oracle Name" in nodes[0].text
    assert "Something" in nodes[0].text


def test_parser_position(parent):
    parser = PositionNodeParser()

    assert parser.node_name == "Position"
    assert parser.regex

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

    # FIXME this doesn't work properly, classes don't get properly checked?
    assert_parser_data(parser, parent, rolls, classes)


def test_parser_progress(parent):
    parser = ProgressNodeParser()

    assert parser.node_name == "Progress"
    assert parser.regex

    classes = ["progress"]

    rolls = [
        ParserData('from=6 name="[[ignored|Track Name]]" rank="dangerous" steps=1', True, 0, classes),
        # allow all kinds of ranks and steps even though they make no sense in practice
        ParserData('from=6 name="[[ignored|Track Name]]" rank="dangerous" steps=100', True, 1, classes),
        ParserData('from=6 name="[[ignored|Track Name]]" rank="unknown" steps=1', True, 2, classes),
        ParserData('from=100 name="[[ignored|Track Name]]" rank="dangerous" steps=1', True, 3, classes),
        # don't allow all else
        ParserData('from=6 name="" rank="dangerous" steps=1', False),
        ParserData('from=6 name="[[ignored]]" rank="dangerous" steps=1', False),
        ParserData('name="[[ignored|Track Name]]" rank="dangerous" steps=1', False),
        ParserData('from=6 rank="dangerous" steps=1', False),
        ParserData('from=6 name="[[ignored|Track Name]]" steps=1', False),
        ParserData('from=6 name="[[ignored|Track Name]]" rank="dangerous"', False),
        ParserData("", False),
        ParserData("random data", False),
    ]

    nodes = assert_parser_data(parser, parent, rolls, classes)
    assert "Track Name" in nodes[0].text


def test_parser_progressroll(parent):
    parser = ProgressRollNodeParser()

    assert parser.node_name == "Progress Roll"
    assert parser.regex

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
        ParserData('name="" score=6 vs1=3 vs2=5', False),
        ParserData('name="[[ignored]]" score=6 vs1=3 vs2=5', False),
        ParserData('score=text vs1=3 vs2=5', False),
        ParserData('score=6 vs1=text vs2=5', False),
        ParserData('score=6 vs1=3 vs2=text', False),
        ParserData('score=-1 vs1=3 vs2=5', False),
        ParserData('score=6 vs1=-1 vs2=5', False),
        ParserData('score=6 vs1=3 vs2=-1', False),
        ParserData(' vs1=3 vs2=5', False),
        ParserData('score=6 vs2=5', False),
        ParserData('score=6 vs1=3', False),
        ParserData("", False),
        ParserData("random data", False)
    ]

    nodes = assert_parser_data(parser, parent, rolls, classes)

    assert "Track Name" in nodes[0].text


def test_parser_reroll(parent):
    parser = RerollNodeParser()

    assert parser.node_name == "Reroll"
    assert parser.regex

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

    assert_parser_data(parser, parent, rolls, classes)


def test_parser_roll(parent):
    parser = RollNodeParser()

    assert parser.node_name == "Roll"
    assert parser.regex

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

    assert_parser_data(parser, parent, rolls, classes)


def test_parser_track(parent):
    parser = TrackNodeParser()

    assert parser.node_name == "Track"
    assert parser.regex

    classes = ["track"]

    rolls = [
        ParserData('name="[[ignored|Track Name]]" status="removed"', True, 0, classes),
        ParserData('name=[[ignored|Track Name]] status="removed"', False),
        ParserData('name="[[ignored|Track Name]]" status=removed', False),
        ParserData('name="" status="removed"', False),
        ParserData('name="[[just a link without name]]" status="removed"', False),
        ParserData('name="[[ignored|Track Name]]" status=""', False),
        ParserData('status="removed"', False),
        ParserData('name="[[ignored|Track Name]]"', False),
        ParserData("", False),
        ParserData("random data", False),
    ]

    nodes = assert_parser_data(parser, parent, rolls, classes)
    assert "Track Name" in nodes[0].text

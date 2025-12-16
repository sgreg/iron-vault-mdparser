import re

from ironvaultmd.util import (
    split_match,
    convert_link_name,
    check_dice,
    check_ticks,
    initiative_slugify,
    position_slugify,
    ticks_to_progress,
)
from utils import StringCompareData, DiceData, ProgressTickData, ProgressBoxTickData


def test_util_split_match():
    raw = "before match after"

    match = re.search("match", raw)
    assert match is not None

    before, after = split_match(raw, match)
    assert before == "before "
    assert after == " after"

    match = re.search(".*match.*", raw)
    assert match is not None

    before, after = split_match(raw, match)
    assert before == ""
    assert after == ""


def test_util_convert_link_name():
    data = [
        StringCompareData("[link name](https://example.org)", "link name"),
        StringCompareData("[linkName](https://example.org)", "linkName"),
        StringCompareData("[link\\/name](https://example.org)", "link/name"),
        StringCompareData("[link/name](https://example.org)", "link/name"),
        StringCompareData("before [link name](https://example.org) after", "before link name after"),
        StringCompareData("before[link name](https://example.org)after", "beforelink nameafter"),
        StringCompareData("[]()", "[]()"),
        StringCompareData("[[link name]]", "link name"),
        StringCompareData("[[linkName]]", "linkName"),
        StringCompareData("[[link\\/name]]", "link/name"),
        StringCompareData("[[link/name]]", "link/name"),
        StringCompareData("before [[link name]] after", "before link name after"),
        StringCompareData("before[[link name]]after", "beforelink nameafter"),
        StringCompareData("[[]]", "[[]]"),
        StringCompareData("[[https://example.org|link name]]", "link name"),
        StringCompareData("[[https://example.org|linkName]]", "linkName"),
        StringCompareData("[[https://example.org|link\\/name]]", "link/name"),
        StringCompareData("[[https://example.org|link/name]]", "link/name"),
        StringCompareData("before [[https://example.org|link name]] after", "before link name after"),
        StringCompareData("before[[https://example.org|link name]]after", "beforelink nameafter"),
        StringCompareData("[[|]]", "[[|]]"),
        StringCompareData("No link in here", "No link in here"),
        StringCompareData("No link in here but \\/ escaped slash", "No link in here but / escaped slash"),
        StringCompareData("", ""),
    ]

    for d in data:
        assert convert_link_name(d.content) == d.expected


def test_util_dice():
    data = [
        DiceData(1, 1, 1, "miss", True),
        DiceData(4, 9, 4, "miss", False),
        DiceData(4, 9, 10, "miss", False),
        DiceData(3, 1, 3, "weak", False),
        DiceData(3, 3, 1, "weak", False),
        DiceData(5, 1, 8, "weak", False),
        DiceData(5, 8, 1, "weak", False),
        DiceData(5, 3, 2, "strong", False),
        DiceData(2, 1, 1, "strong", True),
    ]

    for d in data:
        assert check_dice(d.score, d.vs1, d.vs2) == (d.expected_hitmiss, d.expected_match)


def test_util_ticks():
    data = [
        ProgressTickData("troublesome", 0, 1, (12, 12)),
        ProgressTickData("troublesome", 0, 2, (24, 24)),
        ProgressTickData("troublesome", 0, 3, (36, 36)),
        ProgressTickData("troublesome", 0, 4, (48, 40)),
        ProgressTickData("troublesome", 1, 1, (12, 13)),
        ProgressTickData("troublesome", 12, 1, (12, 24)),
        ProgressTickData("troublesome", 24, 1, (12, 36)),
        ProgressTickData("troublesome", 24, 2, (24, 40)),
        ProgressTickData("troublesome", 36, 1, (12, 40)),
        ProgressTickData("dangerous", 0, 1, (8, 8)),
        ProgressTickData("dangerous", 1, 1, (8, 9)),
        ProgressTickData("dangerous", 8, 1, (8, 16)),
        ProgressTickData("formidable", 0, 1, (4, 4)),
        ProgressTickData("formidable", 1, 1, (4, 5)),
        ProgressTickData("formidable", 4, 1, (4, 8)),
        ProgressTickData("extreme", 0, 1, (2, 2)),
        ProgressTickData("extreme", 1, 1, (2, 3)),
        ProgressTickData("extreme", 2, 1, (2, 4)),
        ProgressTickData("epic", 0, 1, (1, 1)),
        ProgressTickData("epic", 1, 1, (1, 2)),
        ProgressTickData("unknown", 10, 1, (0, 10)),
    ]

    for d in data:
        assert check_ticks(d.rank, d.current, d.steps) == d.expected

def test_util_tick_to_progress():
    data = [
        ProgressBoxTickData(0, (0, 0)),
        ProgressBoxTickData(1, (0, 1)),
        ProgressBoxTickData(4, (1, 0)),
        ProgressBoxTickData(5, (1, 1)),
        ProgressBoxTickData(23, (5, 3)),
        ProgressBoxTickData(40, (10, 0)),
        # No range limitation is put in place, so these should still work
        ProgressBoxTickData(41, (10, 1)),
        ProgressBoxTickData(-1, (0, -1)),
    ]

    for d in data:
        assert ticks_to_progress(d.ticks) == d.expected


def test_util_initiative_slugify():
    data = [
        StringCompareData("out of combat", "nocombat"),
        StringCompareData("has initiative", "initiative"),
        StringCompareData("no initiative", "noinitiative"),
        StringCompareData("invalid initiative", "unknown"),
    ]

    for d in data:
        assert initiative_slugify(d.content) == d.expected

def test_util_position_slugify():
    data = [
        StringCompareData("out of combat", "nocombat"),
        StringCompareData("in control", "control"),
        StringCompareData("in a bad spot", "badspot"),
        StringCompareData("invalid position", "unknown"),
    ]

    for d in data:
        assert position_slugify(d.content) == d.expected

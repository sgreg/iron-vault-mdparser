import re
from ironvaultmd.util import (
    split_match,
    create_div,
    convert_link_name,
    check_dice,
    check_ticks,
)
from utils import CompareData, DiceData, ProgressTickData


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


def test_util_create_dive(parent):
    div_no_classes = create_div(parent)
    div_one_class = create_div(parent, ["class-one"])
    div_multi_classes = create_div(parent, ["class-one", "class-two", "test"])

    assert div_no_classes is not None
    assert div_no_classes.get("class") is None

    assert div_one_class is not None
    assert (classes := div_one_class.get("class")) is not None
    assert classes == "ivm-class-one"

    assert div_multi_classes is not None
    assert (classes := div_multi_classes.get("class")) is not None
    assert classes == "ivm-class-one ivm-class-two ivm-test"


def test_util_convert_link_name():
    data = [
        CompareData[str]("[link name](https://example.org)", "link name"),
        CompareData[str]("[linkName](https://example.org)", "linkName"),
        CompareData[str]("[link\\/name](https://example.org)", "link/name"),
        CompareData[str]("[link/name](https://example.org)", "link/name"),
        CompareData[str]("before [link name](https://example.org) after", "before link name after"),
        CompareData[str]("before[link name](https://example.org)after", "beforelink nameafter"),
        CompareData[str]("[]()", "[]()"),
        CompareData[str]("[[link name]]", "link name"),
        CompareData[str]("[[linkName]]", "linkName"),
        CompareData[str]("[[link\\/name]]", "link/name"),
        CompareData[str]("[[link/name]]", "link/name"),
        CompareData[str]("before [[link name]] after", "before link name after"),
        CompareData[str]("before[[link name]]after", "beforelink nameafter"),
        CompareData[str]("[[]]", "[[]]"),
        CompareData[str]("[[https://example.org|link name]]", "link name"),
        CompareData[str]("[[https://example.org|linkName]]", "linkName"),
        CompareData[str]("[[https://example.org|link\\/name]]", "link/name"),
        CompareData[str]("[[https://example.org|link/name]]", "link/name"),
        CompareData[str]("before [[https://example.org|link name]] after", "before link name after"),
        CompareData[str]("before[[https://example.org|link name]]after", "beforelink nameafter"),
        CompareData[str]("[[|]]", "[[|]]"),
        CompareData[str]("No link in here", "No link in here"),
        CompareData[str]("", ""),
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
        ProgressTickData("troublesome", 0, 1, 12),
        ProgressTickData("troublesome", 0, 2, 24),
        ProgressTickData("troublesome", 0, 3, 36),
        ProgressTickData("troublesome", 0, 4, 40),
        ProgressTickData("troublesome", 1, 1, 13),
        ProgressTickData("troublesome", 12, 1, 24),
        ProgressTickData("troublesome", 24, 1, 36),
        ProgressTickData("troublesome", 24, 2, 40),
        ProgressTickData("troublesome", 36, 1, 40),
        ProgressTickData("dangerous", 0, 1, 8),
        ProgressTickData("dangerous", 1, 1, 9),
        ProgressTickData("dangerous", 8, 1, 16),
        ProgressTickData("formidable", 0, 1, 4),
        ProgressTickData("formidable", 1, 1, 5),
        ProgressTickData("formidable", 4, 1, 8),
        ProgressTickData("extreme", 0, 1, 2),
        ProgressTickData("extreme", 1, 1, 3),
        ProgressTickData("extreme", 2, 1, 4),
        ProgressTickData("epic", 0, 1, 1),
        ProgressTickData("epic", 1, 1, 2),
        ProgressTickData("unknown", 10, 1, 10),
    ]

    for d in data:
        assert check_ticks(d.rank, d.current, d.steps) == d.expected

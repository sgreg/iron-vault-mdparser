import xml.etree.ElementTree as etree
from typing import NamedTuple

from ironvaultmd.parsers.base import NodeParser


class ParserData(NamedTuple):
    content: str
    expected_success: bool
    expected_index: int = 0
    expected_classes: list[str] = []

def assert_parser_data(parser: NodeParser, parent: etree.Element, rolls: list[ParserData], all_classes: list[str]) -> list[etree.Element]:
    # make sure parent has no <div> children at this point
    assert parent.find("div") is None

    for roll in rolls:
        parser.parse(parent, roll.content)

    expected_rolls = [roll for roll in rolls if roll.expected_success]
    nodes = parent.findall("div")

    assert len(nodes) == len(expected_rolls)

    for idx, node in enumerate(nodes):
        roll = expected_rolls[idx]
        classes = node.get("class")

        assert idx == roll.expected_index

        for c in all_classes:
            if c in roll.expected_classes:
                assert c in classes
            else:
                assert c not in classes

    return nodes


class StringCompareData(NamedTuple):
    content: str
    expected: str


class DiceData(NamedTuple):
    score: int
    vs1: int
    vs2: int
    expected_hitmiss: str
    expected_match: bool


class ProgressTickData(NamedTuple):
    rank: str
    current: int
    steps: int
    expected: tuple[int, int]

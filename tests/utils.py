import xml.etree.ElementTree as etree
from typing import NamedTuple

from ironvaultmd.parsers.base import NodeParser
from ironvaultmd.parsers.context import Context


class ParserData(NamedTuple):
    content: str
    expected_success: bool
    expected_index: int = 0
    expected_classes: list[str] = []

def assert_parser_data(parser: NodeParser, ctx: Context, rolls: list[ParserData], all_classes: list[str]) -> list[etree.Element]:
    # make sure parent has no <div> children at this point
    assert ctx.parent.find("div") is None

    for roll in rolls:
        parser.parse(ctx, roll.content)

    nodes = ctx.parent.findall("div")

    # NodeParser creates fallback nodes if regex fails to match,
    # so all items in `rolls` should have an item in `nodes`
    assert len(nodes) == len(rolls)

    success_idx = 0
    for idx, node in enumerate(nodes):
        if rolls[idx].expected_success:
            # Verify the successfully parsed items have the expected index and CSS classes
            roll = rolls[idx]
            classes = node.get("class")

            assert success_idx == roll.expected_index
            success_idx += 1

            for c in all_classes:
                if c in roll.expected_classes:
                    assert c in classes
                else:
                    assert c not in classes
        else:
            # Verify the unsuccessfully parsed items have their text in the fallback node
            assert rolls[idx].content in element_text(node)

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

class ProgressBoxTickData(NamedTuple):
    ticks: int
    expected: tuple[int, int]


def element_text(element: etree.Element) -> str:
    """Extracts and concatenates all text content from an etree element.

    This essentially strips away all inner tags from the HTML string
    and returns the plain text content from it.

    Example:
        `The <b>bold</b> <i>italic</i> frog jumps <sup>over</sup> <span class="something">you know what</span>`
     -> `The bold italic frog jumps over you know what`

    Args:
        element: The HTML element from which to extract the text.

    Returns:
        str: A string containing concatenated text from the `element` and its
        descendants, preserving the order.
    """
    return "".join(text for text in element.itertext())

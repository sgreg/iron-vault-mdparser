import logging
import re

from markdown.blockparser import BlockParser
from markdown.blockprocessors import BlockProcessor
from markdown.preprocessors import Preprocessor

from ironvaultmd.parsers.base import (
    NodeParser,
    FallbackNodeParser,
    MechanicsBlockParser,
    FallbackBlockParser,
    add_roll_result,
)
from ironvaultmd.parsers.blocks import (
    ActorBlockParser,
    MoveBlockParser,
    OracleGroupBlockParser,
    OracleBlockParser,
    OraclePromptBlockParser,
)
from ironvaultmd.parsers.context import Context
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
    TrackNodeParser,
    XpNodeParser,
)
from ironvaultmd.util import add_unhandled_node, create_div, split_match

logger = logging.getLogger("ironvaultmd")


class MechanicsBlockException(Exception):
    pass


class IronVaultMechanicsPreprocessor(Preprocessor):
    """Markdown preprocessor for handling mechanics blocks.

    This serves two purposes:
     1. Convert triple backticks that enclose iron-vault-mechanics blocks to triple commas,
     so this extension can nicely coexist with extensions like fenced_code that would
     otherwise convert those backticks into <pre></pre> content
     2. Make sure iron-vault-mechanics blocks are fully contained within a single `block`
     when passing them on to `IronVaultMechanicsBlockProcessor` by surrounding it with
     newlines, and removing newlines from inside the block
    """

    START = "```iron-vault-mechanics"
    NEW_START = ",,,iron-vault-mechanics"

    END = "```"
    NEW_END = ",,,"

    def run(self, lines: list[str]) -> list[str]: # NOSONAR: don't complain about cognitive complexity, it's a parser after all
        inside = False
        new_lines = []

        for line_num, line in enumerate(lines):
            if line == self.START:
                if inside:
                    raise MechanicsBlockException("Starting block within block")
                inside = True

                if line_num > 0 and lines[line_num - 1] != "":
                    # Append newline before, if there isn't one, to ensure later on that
                    # the mechanics block is at the start of a dedicated BlockParser block
                    new_lines.append("")
                new_lines.append(self.NEW_START)

            elif inside:
                if line == self.END:
                    new_lines.append(self.NEW_END)
                    if line_num + 1 < len(lines) and lines[line_num + 1] != "":
                        # Append newline after, if there isn't one, to ensure later on that
                        # the mechanics block is fully contained within a dedicated BlockParser block
                        new_lines.append("")

                    inside = False

                elif (line := line.strip()) != "":
                    new_lines.append(line)

            else:
                new_lines.append(line)

        logger.debug(new_lines)
        return new_lines


class IronVaultMechanicsBlockProcessor(BlockProcessor):
    # Note, preprocessor removes now all content before and after the mechanics block,
    # so could consider tweaking the regex strings accordingly for these two here.
    # Also, empty but otherwise valid block fails to match now and raises an exception,
    # that's a bit harsh? Could use one common regex here, so test() fails on empty block.
    RE_MECHANICS_START = re.compile(r'(^|\n),,,iron-vault-mechanics(\n|$)')
    RE_MECHANICS_SECTION = re.compile(r'(^|\n),,,iron-vault-mechanics\n(?P<mechanics>[\s\S]*)\n,,,(\n|$)')

    RE_BLOCK_LINE = re.compile(r'^(?P<name>actor|move|oracle-group|oracle|-) (?P<params>[^{]*) \{')
    RE_NODE_LINE = re.compile(r'^(?P<name>add|burn|clock|impact|initiative|meter|move|oracle|position|progress|progress-roll|reroll|roll|track|xp|-) (?P<params>.*)$')

    # Other blocks that exist (see https://ironvault.quest/blocks/index.html)
    #   ...most are actually just for displaying information, which could be considered nice-to-have in the future.
    #   Like displaying character information, the world in its truths, assets in play. The only problem is that
    #   they don't actually display anything, but IV itself renders it then with internal info, hmm...
    #
    #   For fun, try them out in regular text.
    #

    def __init__(self, parser: BlockParser):
        super().__init__(parser)

        self.block_parsers: dict[str, MechanicsBlockParser] = {
            "actor": ActorBlockParser(),
            "move": MoveBlockParser(),
            "oracle-group": OracleGroupBlockParser(),
            "oracle": OracleBlockParser(),
            "-": OraclePromptBlockParser(),
        }

        self.node_parsers: dict[str, NodeParser] = {
            "add": AddNodeParser(),
            "burn": BurnNodeParser(),
            "clock": ClockNodeParser(),
            "impact": ImpactNodeParser(),
            "initiative": InitiativeNodeParser(),
            "meter": MeterNodeParser(),
            "move": MoveNodeParser(),
            "-": OocNodeParser(),
            "oracle": OracleNodeParser(),
            "position": PositionNodeParser(),
            "progress": ProgressNodeParser(),
            "progress-roll": ProgressRollNodeParser(),
            "reroll": RerollNodeParser(),
            "roll": RollNodeParser(),
            "track": TrackNodeParser(),
            "xp": XpNodeParser(),
        }

    def test(self, parent, block) -> bool:
        match = self.RE_MECHANICS_START.search(block)
        logger.debug(f" >>> VLT testing ({'Y' if match is not None else 'N'}) {repr(block)} -> '{match}'")
        return match is not None

    def run(self, parent, blocks) -> None:
        logger.debug(f"\nrun, {len(blocks)} blocks: '{blocks}'")

        block = blocks.pop(0)
        content = ''

        if (match := self.RE_MECHANICS_SECTION.search(block)) is not None:
            # iron-vault-mechanics section found.
            before_mechanics, after_mechanics = split_match(block, match)
            # If the preprocessor works as intended, there shouldn't be
            # anything else around block, as it was supposed to rearrange
            # all that accordingly. So if there is other content, there's
            # need for some logic improvements. Fail hard with prejudice.
            if before_mechanics or after_mechanics:
                raise MechanicsBlockException(f"garbage all around! {repr(block)}")

            content = match.group("mechanics")

        else:
            # If we end up in here, it means test() returned True and
            # therefore found iron-vault-mechanics start section.
            # The preprocessor should have arranged everything to find
            # the entire section's content in there, yet the regex didn't
            # match that here. Something is wrong. Fail hard.
            raise MechanicsBlockException(f"your logic sucks, {repr(block)}")

        logger.debug(f"mechanics block content: {repr(content)}")
        element = create_div(parent, ["mechanics"])
        ctx = Context(element)
        self.parse_content(ctx, content)

    def parse_content(self, ctx: Context, content: str, indent=0) -> None:
        logger.debug(f"x> adding content {repr(content)}")

        lines = [chunk for chunk in content.split("\n") if chunk]
        for idx, line in enumerate(lines):
            logger.debug(f"line #{idx: 2d}: '{line}'")

            if (block_match := self.RE_BLOCK_LINE.search(line)) is not None:
                name = block_match.group("name")
                data = block_match.group("params")

                parser = self.block_parsers.get(name)

                if parser is None:
                    parser = FallbackBlockParser(name)
                    add_unhandled_node(f"{name} block")

                element = parser.create_element(ctx, data)
                ctx.push(element)

            elif (node_match := self.RE_NODE_LINE.search(line)) is not None:
                name = node_match.group("name")
                data = node_match.group("params")

                parser = self.node_parsers.get(name)

                if parser is None:
                    parser = FallbackNodeParser(name)
                    add_unhandled_node(name)

                parser.parse(ctx, data)

            elif line == '}':
                add_roll_result(ctx)
                ctx.pop()

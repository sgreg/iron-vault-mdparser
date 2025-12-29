"""Mechanics block processors for Iron Vault Markdown.

This module contains a preprocessor and a block processor to support fenced
mechanics sections in Markdown documents. Mechanics sections are fenced with
```iron-vault-mechanics and describe game actions which are parsed into an
intermediate representation using dedicated block and node parsers.

The preprocessor normalizes fencing so that the block processor can reliably
detect and consume entire mechanics sections as a single block.
"""

import logging
import re

from markdown.blockparser import BlockParser
from markdown.blockprocessors import BlockProcessor
from markdown.preprocessors import Preprocessor

from ironvaultmd import logger_name
from ironvaultmd.parsers.base import (
    NodeParser,
    MechanicsBlockParser,
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
from ironvaultmd.util import split_match

logger = logging.getLogger(logger_name)


class MechanicsBlockException(Exception):
    """Raised when a mechanics block is malformed or inconsistent."""


class IronVaultMechanicsPreprocessor(Preprocessor):
    """Markdown preprocessor for handling mechanics blocks.

    This serves two purposes:

     1. Convert triple backticks that enclose iron-vault-mechanics blocks to triple commas,
        so this extension can nicely coexist with extensions like fenced_code that would
        otherwise convert those backticks into `<pre></pre>` content
     2. Make sure iron-vault-mechanics blocks are fully contained within a single `block`
        when passing them on to `IronVaultMechanicsBlockProcessor` by surrounding it with
        newlines, and removing newlines from inside the block
    """

    START = "```iron-vault-mechanics"
    NEW_START = ",,,iron-vault-mechanics"

    END = "```"
    NEW_END = ",,,"

    def run(self, lines: list[str]) -> list[str]: # NOSONAR don't complain about cognitive complexity, it's a parser after all
        """Rewrite mechanics fences and ensure block boundaries.

        Converts triple backticks around mechanics blocks to triple commas to
        avoid collisions with other Markdown extensions and ensures that a
        mechanics block is isolated as its own parser block by inserting blank
        lines before and after the fenced section.

        Args:
            lines: The Markdown document, split into lines.

        Returns:
            The normalized list of lines.

        Raises:
            MechanicsBlockException: If nested mechanics blocks are detected.
        """
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
    """Block processor that parses mechanics sections.

    The processor identifies mechanics sections normalized by
    `IronVaultMechanicsPreprocessor` and iterates over their content, delegating
    to specific block and node parsers based on their line prefixes.

    Attributes:
        RE_MECHANICS_START: Regex to detect the start fence of a mechanics block.
        RE_MECHANICS_SECTION: Regex to capture the entire mechanics section
            content including start and end fences.
        RE_BLOCK_LINE: Regex used to detect the start of a mechanics subblock.
        RE_NODE_LINE: Regex used to detect mechanics node lines within a block.
        block_parsers: Mapping of block names to `MechanicsBlockParser` instances.
        node_parsers: Mapping of node names to `NodeParser` instances.
    """
    # Note, preprocessor removes now all content before and after the mechanics block,
    # so could consider tweaking the regex strings accordingly for these two here.
    # Also, empty but otherwise valid block fails to match now and raises an exception,
    # that's a bit harsh? Could use one common regex here, so test() fails on empty block.
    RE_MECHANICS_START = re.compile(r'(^|\n),,,iron-vault-mechanics(\n|$)')
    RE_MECHANICS_SECTION = re.compile(r'(^|\n),,,iron-vault-mechanics\n(?P<mechanics>[\s\S]*)\n,,,(\n|$)')

    RE_BLOCK_LINE = re.compile(r'^(?P<name>actor|move|oracle-group|oracle|-) (?P<params>[^{]*) \{')
    RE_NODE_LINE = re.compile(r'^(?P<name>add|burn|clock|impact|initiative|meter|move|oracle|position|progress|progress-roll|reroll|roll|track|xp|-) (?P<params>.*)$')
    RE_OOC_LINE = re.compile(r'^- "[^"]*$')

    # Other blocks that exist (see https://ironvault.quest/blocks/index.html)
    #   ...most are actually just for displaying information, which could be considered nice-to-have in the future.
    #   Like displaying character information, the world in its truths, assets in play. The only problem is that
    #   they don't actually display anything, but IV itself renders it then with internal info, hmm...
    #
    #   For fun, try them out in regular text.
    #

    def __init__(self, parser: BlockParser):
        """Initialize the block and node parser registries.

        Args:
            parser: The Markdown `BlockParser` that owns this processor.
        """
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
        """Return whether the given block begins a mechanics section.

        Args:
            parent: The parent HTML element (unused).
            block: The text block to test.

        Returns:
            True if the block contains a mechanics start fence; otherwise False.
        """
        match = self.RE_MECHANICS_START.search(block)
        logger.debug(f" >>> VLT testing ({'Y' if match is not None else 'N'}) {repr(block)} -> '{match}'")
        return match is not None

    def run(self, parent, blocks) -> None:
        """Process a mechanics section and append the rendered result.

        Args:
            parent: The parent HTML element to which the output is appended.
            blocks: The list of remaining text blocks; the current block is
                consumed from this list.

        Raises:
            MechanicsBlockException: If the section cannot be isolated or is
                otherwise malformed.
        """
        logger.debug(f"\nrun, {len(blocks)} blocks: '{blocks}'")

        block = blocks.pop(0)
        content = ''

        if (match := self.RE_MECHANICS_SECTION.search(block)) is not None:
            # iron-vault-mechanics section found.
            before_mechanics, after_mechanics = split_match(block, match)
            # If the preprocessor works as intended, there shouldn't be
            # anything else around block, as it was supposed to rearrange
            # all that accordingly. So if there is other content, there's
            # need for some logic improvements. Fail hard.
            if before_mechanics or after_mechanics:
                raise MechanicsBlockException(f"Unexpected content around match block: {repr(block)}")

            content = match.group("mechanics")

        else:
            # If we end up in here, it means test() returned True and
            # therefore found iron-vault-mechanics start section.
            # The preprocessor should have arranged everything to find
            # the entire section's content in there, yet the regex didn't
            # match that here. Something is wrong. Fail hard.
            raise MechanicsBlockException(f"Mechanics block matching failed: {repr(block)}")

        logger.debug(f"mechanics block content: {repr(content)}")
        ctx = Context(parent)
        self.parse_content(ctx, content)

    def parse_content(self, ctx: Context, content: str) -> None:
        """Parse mechanics content lines using block and node parsers.

        Args:
            ctx: The parsing context carrying the current HTML element and stack.
            content: The raw mechanics section content (without fences).
        """
        logger.debug(f"x> adding content {repr(content)}")

        multiline_ooc = None

        lines = [chunk for chunk in content.split("\n") if chunk]
        for idx, line in enumerate(lines):
            logger.debug(f"line #{idx: 2d}: '{line}'")

            # Check for multiline out-of-character comments, i.e., a OOC line without closing quotes.
            # If found, collect all the next lines until the closing quote is found at the end of a line.
            # Merge into a single line separated with <br> and proceed with the regular line parsing.
            if (ooc_match := self.RE_OOC_LINE.search(line)) is not None:
                multiline_ooc = [ooc_match.group(0)]
                continue
            elif multiline_ooc is not None:
                multiline_ooc.append(line)
                if line[-1] != '"':
                    continue
                line = "<br>".join(multiline_ooc)
                multiline_ooc = None


            if (block_match := self.RE_BLOCK_LINE.search(line)) is not None:
                name = block_match.group("name")
                data = block_match.group("params")

                parser = self.block_parsers.get(name)
                parser.begin(ctx, data)

            elif (node_match := self.RE_NODE_LINE.search(line)) is not None:
                name = node_match.group("name")
                data = node_match.group("params")

                parser = self.node_parsers.get(name)
                parser.parse(ctx, data)

            elif line == '}':
                parser = self.block_parsers.get(ctx.names.parser)
                parser.finalize(ctx)

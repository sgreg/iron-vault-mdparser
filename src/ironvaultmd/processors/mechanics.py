import re
import xml.etree.ElementTree as etree

from markdown.blockprocessors import BlockProcessor
from markdown.preprocessors import Preprocessor

from ironvaultmd.parsers.base import NodeParser
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
from ironvaultmd.util import add_unhandled_node, create_div, split_match


class MechanicsBlockException(Exception):
    pass


class IronVaultMechanicsPreprocessor(Preprocessor):
    """Markdown preprocessor for handling mechanics blocks.

    This serves two purposes:
     1. Convert triple backticks that enclose iron-vault-mechnics blocks to triple commas,
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

        print(new_lines)
        return new_lines


class IronVaultMechanicsBlockProcessor(BlockProcessor):
    # Note, preprocessor removes now all content before and after the mechanics block,
    # so could consider tweaking the regex strings accordingly for these two here.
    # Also, empty but otherwise valid block fails to match now and raises an exception,
    # that's a bit harsh? Could use one common regex here, so test() fails on empty block.
    RE_MECHANICS_START = re.compile(r'(^|\n),,,iron-vault-mechanics(\n|$)')
    RE_MECHANICS_SECTION = re.compile(r'(^|\n),,,iron-vault-mechanics\n(?P<mechanics>[\s\S]*)\n,,,(\n|$)')

    # note, this exists also for
    #  - oracle-group { oracle ...\noracle ... }  e.g. create entity/character or somethin
    #  - actor name=[[link|name]] { move {} }  for when "Always record actor" (or multiplayer?) is enabled
    # Should probably collect all content into a data object to e.g. match a roll to a move or a reroll to a previous roll
    RE_MOVE_NODE = re.compile(r'move +"\[(?P<move_name>[^\]]+)\]\((?P<move_link>[^)]+)\)" +\{(?P<move_content>[\s\S]*)}')
    RE_CMD_NODE_CHECK = re.compile(r'(^|\n)(\b(roll|reroll|progress_roll|progress|meter|track|clock|burn|add|position|oracle)\b|- "[^"]*")')

    RE_CMD = re.compile(r'^\s*(?P<cmd_name>[\S]{2,}) +(?P<cmd_params>\S[\S ]*)$')
    RE_OOC = re.compile(r'^\s*- +"(?P<ooc>[^"]*)"$')

    parsers: dict[str, NodeParser] = {
        "add": AddNodeParser(),
        "burn": BurnNodeParser(),
        "clock": ClockNodeParser(),
        "meter": MeterNodeParser(),
        "ooc": OocNodeParser(),
        "oracle": OracleNodeParser(),
        "position": PositionNodeParser(),
        "progress": ProgressNodeParser(),
        "progress-roll": ProgressRollNodeParser(),
        "reroll": RerollNodeParser(),
        "roll": RollNodeParser(),
        "track": TrackNodeParser(),
    }

    def test(self, parent, block) -> bool:
        match = self.RE_MECHANICS_START.search(block)
        print(f" >>> VLT testing ({'Y' if match is not None else 'N'}) {repr(block)} -> '{match}'")
        return match is not None

    def run(self, parent, blocks) -> None:
        print(f"\nrun, {len(blocks)} blocks: '{blocks}'")

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

        print(f"mechanics block content: {repr(content)}")
        element = create_div(parent, ["mechanics"])
        self.parse_content(element, content)


    def parse_content(self, parent, content: str, indent=0) -> None:
        print(f"x> adding content {repr(content)}")

        if (move_node_match := self.RE_MOVE_NODE.search(content)) is not None:
            print(f"{" " * indent}MOVE: {move_node_match.group("move_name")}")
            element = create_div(parent, ["move"])
            create_div(element, ["move-name"]).text = f"{move_node_match.group("move_name")}"

            self.parse_content(element, move_node_match.group("move_content"), indent + 4)

            # if there's afterwards more, grab it and re-parse that, too
            _, after = split_match(content, move_node_match)
            if after:
                self.parse_content(parent, after, indent)

        elif self.RE_CMD_NODE_CHECK.search(content) is not None:
            # Note: this only verifies valid comments for the very first line
            #       after it passes the first check, the line splitting here is
            #       only interested if it matches "<words> <words>"
            #       Should add checks for each line then.
            lines = [c for c in content.split("\n") if c]

            for line in lines:
                if (cmd_match := self.RE_CMD.search(line)) is not None:
                    print(f"{" " * indent}CMD: {cmd_match.group("cmd_name")}({cmd_match.group("cmd_params")})")
                    element = create_div(parent, ["node"])
                    name = cmd_match.group("cmd_name")
                    data = cmd_match.group("cmd_params")

                elif (ooc_match := self.RE_OOC.search(line)) is not None:
                    print(f"{" " * indent}// {ooc_match.group("ooc")}")
                    element = parent
                    name = "ooc"
                    data = ooc_match.group("ooc")

                else:
                    print(f"skipping unknown content {repr(line)}")
                    continue

                self.add_node(element, name, data)


    def add_node(self, parent: etree.Element, name: str, data: str) -> None:
        parser = self.parsers.get(name)

        if parser is None:
            parser = NodeParser(name)
            add_unhandled_node(name)

        parser.parse(parent, data)
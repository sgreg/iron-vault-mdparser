# Python-Markdown extension for iron-vault markdown blocks

"""
Convert iron-vault markdown blocks, such as iron-vault-mechanics to dedicated html css classes and whatnot .. dunno yet, let's see what else?
"""

import re
from typing import Any
import yaml
import xml.etree.ElementTree as etree

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.blockprocessors import BlockProcessor

class FrontmatterException(Exception):
    pass

class IronVaultFrontmatterPreprocessor(Preprocessor):
    """Markdown preprocessor for handling Obsidian frontmatter data.

    If the markdown content begins with `---`, all content until the closing
    pair of `---` is collected separately, removed from the markdown data itself,
    and parsed as YAML content. The resulting dictionary is then stored within
    the `md` instance as `md.Frontmatter`.
    """
    FRONTMATTER_DELIMITER = "---"

    def run(self, lines: list[str]) -> list[str]:
        # Frontmatter information is YAML content at the very beginning of the file.
        # Check if the very first line is the frontmatter delimiter, if not, do nothing.
        if lines[0] != self.FRONTMATTER_DELIMITER:
            # No frontmatter in file, return lines as is
            return lines
        
        # File has frontmatter
        # Remove first line containing the starting delimiter
        lines.pop(0)

        yaml_lines = []
        while lines:
            # Loop through markdown until ending delimiter is found,
            # move content from markdown to separate yaml_lines array.
            line = lines.pop(0)
            if line == self.FRONTMATTER_DELIMITER:
                # End of frontmatter, break out of the loop
                break
            yaml_lines.append(line)
        else:
            # Loop ended without finding frontmatter end delimiter.
            # This is kinda bad, but also means the file is misformated.
            raise FrontmatterException("Frontmatter ending delimiter not found")

        # Create YAML content from extracted lines, parse it, and store internally
        yaml_text = '\n'.join(yaml_lines)
        frontmatter = yaml.safe_load(yaml_text)
        self.md.Frontmatter = frontmatter

        return lines


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


class NodeParser:
    """Most elemental base parser for iron-vault-mechanics nodes"""
    
    def __init__(self, name: str) -> None:
        self.node_name = name
        

    def parse(self, parent: etree.Element, data: str) -> None:
        """Parse the given data, create HTML elements from it, and attach it to the given parent element"""
        parent.text = f"<i>{self.node_name}</i>: {data}"


class RegexNodeParser(NodeParser):
    """Parser for iron-vault-mechanics nodes supporting regex matching"""
    regex: re.Match
    
    def __init__(self, name: str, regex: str) -> None:
        super().__init__(name)
        self.regex = re.compile(regex)

    def __match(self, data: str) -> dict[str, str | Any] | None:
        """Try to match the given data string to the parser's regex object and return match group dictionary"""
        match = self.regex.search(data)
        
        if match is None:
            print(f"Fail to match parameters for {self.node_name}: {repr(data)}")
            return None
    
        print(match)
        return match.groupdict()

    def parse(self, parent: etree.Element, data: str) -> None:
        p = self.__match(data)
        if p is None:
            return
        
        self.set_element(parent, p)
    
    def set_element(self, parent: etree.Element, data: dict[str, str | Any]) -> None:
        """Parser subclass specific method to set element data to the given parent element"""
        raise NotImplementedError
    
    
class SimpleContentNodeParser(RegexNodeParser):
    """Parser for iron-vault-mechanics nodes to simply set node content text"""
    def __init__(self, name: str, regex: str, divs: list[str]) -> None:
        self.divs = divs
        super().__init__(name, regex)
        
    def set_element(self, parent: etree.Element, data: dict[str, str | Any]) -> None:
        """Create `<div>` element object with the CSS classes passed to the constructor and call set_content"""
        element = create_div(parent, self.divs)
        self.set_content(element, data)
    
    def set_content(self, element: etree.Element, data: dict[str, str | Any]) -> None:
        """Parser subclass specific method to set up the given element's content"""
        raise NotImplementedError
    

class OocNodeParser(NodeParser):
    """iron-vault-mechanics out-of-character notes node parser"""
    def __init__(self) -> None:
        super().__init__("OOC")

    def parse(self, parent: etree.Element, data: str) -> None:
        element = create_div(parent, ["ooc"])
        element.text = f"// {data}"


class RollNodeParser(RegexNodeParser):
    def __init__(self) -> None:
        regex = r'^"(?P<stat_name>\w*)" action=(?P<action>\d+) adds=(?P<adds>\d+) stat=(?P<stat>\d+) vs1=(?P<vs1>\d+) vs2=(?P<vs2>\d+)$'
        super().__init__("Roll", regex)

    def set_element(self, parent, data) -> None:
        total = min(int(data["action"]) + int(data["stat"]) + int(data["adds"]), 10)
        vs1 = int(data["vs1"])
        vs2 = int(data["vs2"])

        hitmiss, match = check_dice(total, vs1, vs2)

        element = create_div(parent, ["roll", f"roll-{hitmiss}", "roll-match" if match else ""])
        # Consider for all those some user-overridable function that this is passed on to 
        # e.g. functions like set_roll_node_element(parent, name, action, stat, adds, vs1, vs2)
        # so users can define themselves how to set or otherwise style the content.
        # e.g. have "Roll with <span ...>Edge</span> .. " or whatever else.
        element.text = f"Roll with {data["stat_name"]}: {data["action"]} + {data["stat"]} + {data["adds"]} = {total} vs {data["vs1"]} | {data["vs2"]} {hitmiss} {"WITH MATCH!" if match else ""}"


class RerollNodeParser(SimpleContentNodeParser):
    def __init__(self) -> None:
        # reroll action="5"
        # reroll vs1="3"
        # reroll vs2="4"
        regex = r'^(?P<dice>action|vs1|vs2)="(?P<value>\d+)"$'
        super().__init__("Roll", regex, ["reroll"])

    def set_content(self, element, data) -> None:
        element.text = f"Reroll {data["dice"]} &rarr; {data["value"]}"


class ProgressRollNodeParser(RegexNodeParser):
    def __init__(self) -> None:
        # progress-roll name="[[Lone Howls\/Progress\/Combat Tayla.md|Combat Tayla]]" score=8 vs1=1 vs2=4
        # Note, before Dec 2024, name parameter may be missing, so pack the whole 'name="[[..|..]]" ' into optional group '(?: ...)?'
        regex = r'^(?:name="\[\[.*\|(?P<name>.*)\]\]" )?score=(?P<score>\d+) vs1=(?P<vs1>\d+) vs2=(?P<vs2>\d+)$'
        super().__init__("Progress Roll", regex)

    def set_element(self, parent, data) -> None:
        score = int(data["score"])
        vs1 = int(data["vs1"])
        vs2 = int(data["vs2"])

        hitmiss, match = check_dice(score, vs1, vs2)

        element = create_div(parent, ["roll", f"roll-{hitmiss}", "roll-match" if match else ""])
        element.text = f"<i>Roll Progress</i> for {data['name'] if data['name'] is not None else 'undefined'}: {data["score"]} vs {data["vs1"]} | {data["vs2"]} {hitmiss} {"WITH MATCH!" if match else ""}"


class ProgressNodeParser(SimpleContentNodeParser):
    def __init__(self) -> None:
        # progress: from=8 name="[[Lone Howls\/Progress\/Connection Dykstra.md|Connection Dykstra]]" rank="dangerous" steps=1
        regex = r'^from=(?P<from>\d+) name="\[\[.*\|(?P<name>.*)\]\]" rank="(?P<rank>\w+)" steps=(?P<steps>\d+)$'
        super().__init__("Progress", regex, ["progress"])

    def set_content(self, element, data) -> None:
        ticks = check_ticks(data["rank"], int(data["from"]), int(data['steps']))
        element.text = f"<i>Progress</i> for {data['name']} ({data["rank"]}): {data["from"]} -> {ticks}"
    

class MeterNodeParser(RegexNodeParser):
    def __init__(self) -> None:
        # meter "Momentum" from=5 to=6
        regex = r'^"(?P<meter_name>\w+)" from=(?P<from>\d+) to=(?P<to>\d+$)'
        super().__init__("Meter", regex)
        
    def set_element(self, parent, data) -> None:
        oldval = int(data['from'])
        newval = int(data['to'])

        element = create_div(parent, ["meter", "meter-increase" if newval > oldval else "meter-decrease"])
        element.text = f"<i>{data['meter_name']}</i>: {data['from']} &rarr; {data['to']}"


class TrackNodeParser(SimpleContentNodeParser):
    def __init__(self) -> None:
        # track name="[[Lone Howls\/Progress\/Combat Tayla.md|Combat Tayla]]" status="removed"
        regex = r'^name="\[\[.*\|(?P<track_name>.*)\]\]" status="(?P<status>\w+)"$'
        super().__init__("Track", regex, ["track"])

    def set_content(self, element, data) -> None:
        element.text = f"Track <i>{data['track_name']}</i> {data["status"]}"


class ClockNodeParser(SimpleContentNodeParser):
    def __init__(self) -> None:
        # clock from=2 name="[[Lone Howls\/Clocks\/Titanhold Bounty Hunters closing in on Dykstra.md|Titanhold Bounty Hunters closing in on Dykstra]]" out-of=6 to=3
        regex = r'^from=(?P<from>\d+) name="\[\[.*\|(?P<name>.*)\]\]" out-of=(?P<segments>\d+) to=(?P<filled>\d+)$'
        super().__init__("Clock", regex, ["clock"])

    def set_content(self, element, data) -> None:
        element.text = f"<i>Clock</i> for {data['name']} -> {data["filled"]} / {data["segments"]}"
        

class BurnNodeParser(SimpleContentNodeParser):
    def __init__(self) -> None:
        # burn from=8 to=2
        regex = r'^from=(?P<from>\d+) to=(?P<to>\d+)$'
        super().__init__("Burn", regex, ["meter", "meter-burn"])

    def set_content(self, element: etree.Element, data: dict[str, str | Any]) -> None:
        element.text = f"<i>Burn Momentum</i>: {data['from']} &rarr; {data['to']}"


class AddNodeParser(SimpleContentNodeParser):
    def __init__(self) -> None:
        # add 1 "Tech asset"   or just
        # add 1
        regex = r'^(?P<add>\d+)(?: "(?P<comment>.+)")?$'
        super().__init__("Add", regex, ["add"])

    def set_content(self, element: etree.Element, data: dict[str, str | Any]) -> None:
        comment = f" ({data['comment']})" if data['comment'] else ""
        element.text = f"Add +{data['add']}{comment}"


class PositionNodeParser(RegexNodeParser):
    def __init__(self) -> None:
        #position from="out of combat" to="in control"
        regex = r'^from="(?P<from>.+)" to="(?P<to>.+)"$'
        super().__init__("Position", regex)
        
    def set_element(self, parent, data) -> None:
        match data["to"]:
            case "out of combat":
                position = "nocombat"
            case "in control":
                position = "control"
            case "in a bad spot":
                position = "badspot"

        element = create_div(parent, ["position", f"position-{position}"])
        element.text = f"Position {data['from']} &rarr; {data['to']}"


class OracleNodeParser(SimpleContentNodeParser):
    def __init__(self) -> None:
        # oracle name="[Core Oracles \/ Theme](datasworn:oracle_rollable:starforged\/core\/theme)" result="Warning" roll=96
        regex = r'^name="\[(?P<oracle_name>.+)\]\(datasworn:.+\)" result="(?P<result>.+)" roll=(?P<roll>\d+)$'
        super().__init__("Oracle", regex, ["oracle"])
        
    def set_content(self, parent, data) -> None:
        oracle = data["oracle_name"].replace("\\/", "/")
        parent.text = f"Oracle <i>{oracle}</i> rolled a {data['roll']} == {data['result']}"



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
    RE_MOVE_NODE = re.compile(r'move\s+"\[(?P<move_name>[\s\S]*)\]\((?P<move_link>[\s\S]*)\)"\s*\{(?P<move_content>[\s\S]*)}')
    RE_CMD_NODE_CHECK = re.compile(r'(^|[\s]*)(roll|reroll|progress_roll|progress|meter|track|clock|burn|add|position|oracle|\s*-\s*")')

    RE_CMD = re.compile(r'^\s*(?P<cmd_name>[\S]{2,}) +(?P<cmd_params>[\s\S]+)$')
    RE_OOC = re.compile(r'^\s*- +"(?P<ooc>[\s\S]+)"$')
        

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
        parser: NodeParser

        match name:
            case "ooc":
                parser = OocNodeParser()
            case "roll":
                parser = RollNodeParser()
            case "reroll":
                parser = RerollNodeParser()
            case "progress-roll":
                parser = ProgressRollNodeParser()
            case "progress":
                parser = ProgressNodeParser()
            case "meter":
                parser = MeterNodeParser()
            case "track":
                parser = TrackNodeParser()
            case "clock":
                parser = ClockNodeParser()
            case "burn":
                parser = BurnNodeParser()
            case "add":
                parser = AddNodeParser()
            case "position":
                parser = PositionNodeParser()
            case "oracle":
                parser = OracleNodeParser()
            case _:
                add_unhandled_node(name)
                parser = NodeParser(name)
        
        parser.parse(parent, data)


#
#           UTIL FUNCTIONS
#

def split_match(text: str, match: re.Match[str]) -> tuple[str, str]:
    """Split a regex match to extract and return any text before and after the match"""
    before = text[:match.start()]
    after = text[match.end():]
    return (before, after)


def create_div(parent: etree.Element, classes: list[str] | None = None) -> etree.Element:
    """Create and return an etree.Element `<div>` with an optional list of class identifiers"""
    e = etree.SubElement(parent, "div")
    
    if classes is not None:
        ivm_classes = ["ivm-" + c for c in classes if c]
        e.set("class", " ".join(ivm_classes))

    return e

unhandled_nodes: list[str] = []
def add_unhandled_node(node: str) -> None:
    """Keep track of iron-vault-mechanics nodes that aren't handled yet (for dev purpose only)"""
    if node not in unhandled_nodes:
        unhandled_nodes.append(node)


def check_dice(score, vs1, vs2) -> tuple[str, bool]:
    """Check dice values against each other and return hit/miss and match situation of it"""
    if score > vs1 and score > vs2:
        hitmiss = "strong"
    elif score > vs1 or score > vs2:
        hitmiss = "weak"
    else:
        hitmiss = "miss"
    
    match = (vs1 == vs2)
    return (hitmiss, match)


def check_ticks(rank: str, current: int, steps: int) -> int:
    """Check and return new progress track ticks value"""
    ticks = 0
    match rank:
        case "epic":
            ticks = 1
        case "extreme":
            ticks = 2
        case "formidable":
            ticks = 4
        case "dangerous":
            ticks = 8
        case "troublesome":
            ticks = 12
        case _:
            print(f"Fail to check ticks, unknown rank {rank}")
            return current
        
    return current + (ticks * steps)

        

class IronVaultExtension(Extension):
    def extendMarkdown(self, md) -> None:
        md.registerExtension(self)
        self.md = md

        # fenced_code preprocessor has priority 25, ours must have higher one to make sure it's runs first
        md.preprocessors.register(IronVaultMechanicsPreprocessor(md), 'ironvault-mechanics-preprocessor', 50)
        md.preprocessors.register(IronVaultFrontmatterPreprocessor(md), 'ironvault-frontmatter-preprocessor', 40)
        md.parser.blockprocessors.register(IronVaultMechanicsBlockProcessor(md.parser), 'ironvault-mechanics', 175)
    
    def reset(self) -> None:
        self.md.Frontmatter = {}

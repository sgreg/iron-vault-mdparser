import xml.etree.ElementTree as etree
from typing import Any

from ironvaultmd.parsers.base import (
    NodeParser,
    RegexNodeParser,
    SimpleContentNodeParser,
)
from ironvaultmd.util import check_dice, check_ticks, create_div, convert_link_name


class AddNodeParser(SimpleContentNodeParser):
    def __init__(self) -> None:
        # add 1 "Tech asset"   or just
        # add 1
        regex = r'^(?P<add>\d+)(?: "(?P<comment>.+)")?$'
        super().__init__("Add", regex, ["add"])

    def set_content(self, element: etree.Element, data: dict[str, str | Any]) -> None:
        comment = f" ({data['comment']})" if data['comment'] else ""
        element.text = f"Add +{data['add']}{comment}"


class BurnNodeParser(SimpleContentNodeParser):
    def __init__(self) -> None:
        # burn from=8 to=2
        regex = r'^from=(?P<from>\d+) to=(?P<to>\d+)$'
        super().__init__("Burn", regex, ["meter", "meter-burn"])

    def set_content(self, element: etree.Element, data: dict[str, str | Any]) -> None:
        element.text = f"<i>Burn Momentum</i>: {data['from']} &rarr; {data['to']}"


class ClockNodeParser(SimpleContentNodeParser):
    def __init__(self) -> None:
        # clock from=2 name="[[Lone Howls\/Clocks\/Titanhold Bounty Hunters closing in on Dykstra.md|Titanhold Bounty Hunters closing in on Dykstra]]" out-of=6 to=3
        regex = r'^from=(?P<from>\d+) name="\[\[.*\|(?P<name>.*)\]\]" out-of=(?P<segments>\d+) to=(?P<filled>\d+)$'
        super().__init__("Clock", regex, ["clock"])

    def set_content(self, element, data) -> None:
        element.text = f"<i>Clock</i> for {data['name']} -> {data["filled"]} / {data["segments"]}"


class MeterNodeParser(RegexNodeParser):
    def __init__(self) -> None:
        # meter "Momentum" from=5 to=6
        regex = r'^"(?P<meter_name>\w+)" from=(?P<from>\d+) to=(?P<to>\d+$)'
        super().__init__("Meter", regex)

    def set_element(self, parent, data) -> None:
        oldval = int(data['from'])
        newval = int(data['to'])

        classes = ["meter"]
        if newval > oldval:
            classes.append("meter-increase")
        elif newval < oldval:
            classes.append("meter-decrease")

        element = create_div(parent, classes)
        element.text = f"<i>{data['meter_name']}</i>: {data['from']} &rarr; {data['to']}"


class OocNodeParser(NodeParser):
    """iron-vault-mechanics out-of-character notes node parser"""
    def __init__(self) -> None:
        super().__init__("OOC")

    def parse(self, parent: etree.Element, data: str) -> None:
        element = create_div(parent, ["ooc"])
        element.text = f"// {data}"


class OracleNodeParser(SimpleContentNodeParser):
    def __init__(self) -> None:
        # oracle name="[Core Oracles \/ Theme](datasworn:oracle_rollable:starforged\/core\/theme)" result="Warning" roll=96
        # oracle name="Will [[Lone Howls\/Clocks\/Clock decrypt Verholm research.md|Clock decrypt Verholm research]] advance? (Likely)" result="No" roll=83
        regex = r'^name="(\[(?P<oracle_name>[^\]]+)\]\(datasworn:.+\)|(?P<oracle_text>[^"]+))" result="(?P<result>[^"]+)" roll=(?P<roll>\d+)$'
        super().__init__("Oracle", regex, ["oracle"])

    def set_content(self, parent, data) -> None:
        oracle = "undefined"
        if data["oracle_name"] is not None:
            oracle = convert_link_name(data["oracle_name"])
        elif data["oracle_text"] is not None:
            oracle = convert_link_name(data["oracle_text"])

        parent.text = f"Oracle <i>{oracle}</i> rolled a {data['roll']} == {data['result']}"


class PositionNodeParser(RegexNodeParser):
    def __init__(self) -> None:
        #position from="out of combat" to="in control"
        regex = r'^from="(?P<from>.+)" to="(?P<to>.+)"$'
        super().__init__("Position", regex)

    def set_element(self, parent, data) -> None:
        classes = ["position"]

        match data["to"]:
            case "out of combat":
                classes.append("position-nocombat")
            case "in control":
                classes.append("position-control")
            case "in a bad spot":
                classes.append("position-badspot")

        element = create_div(parent, classes)
        element.text = f"Position {data['from']} &rarr; {data['to']}"


class ProgressNodeParser(SimpleContentNodeParser):
    def __init__(self) -> None:
        # progress: from=8 name="[[Lone Howls\/Progress\/Connection Dykstra.md|Connection Dykstra]]" rank="dangerous" steps=1
        regex = r'^from=(?P<from>\d+) name="\[\[.*\|(?P<name>.*)\]\]" rank="(?P<rank>\w+)" steps=(?P<steps>\d+)$'
        super().__init__("Progress", regex, ["progress"])

    def set_content(self, element, data) -> None:
        ticks = check_ticks(data["rank"], int(data["from"]), int(data['steps']))
        element.text = f"<i>Progress</i> for {data['name']} ({data["rank"]}): {data["from"]} -> {ticks}"


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


class RerollNodeParser(SimpleContentNodeParser):
    def __init__(self) -> None:
        # reroll action="5"
        # reroll vs1="3"
        # reroll vs2="4"
        regex = r'^(?P<dice>action|vs1|vs2)="(?P<value>\d+)"$'
        super().__init__("Reroll", regex, ["reroll"])

    def set_content(self, element, data) -> None:
        element.text = f"Reroll {data["dice"]} &rarr; {data["value"]}"


class RollNodeParser(RegexNodeParser):
    def __init__(self) -> None:
        regex = r'^"(?P<stat_name>\w+)" action=(?P<action>\d+) adds=(?P<adds>\d+) stat=(?P<stat>\d+) vs1=(?P<vs1>\d+) vs2=(?P<vs2>\d+)$'
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


class TrackNodeParser(SimpleContentNodeParser):
    def __init__(self) -> None:
        # track name="[[Lone Howls\/Progress\/Combat Tayla.md|Combat Tayla]]" status="removed"
        regex = r'^name="\[\[.*\|(?P<track_name>.*)\]\]" status="(?P<status>\w+)"$'
        super().__init__("Track", regex, ["track"])

    def set_content(self, element, data) -> None:
        element.text = f"Track <i>{data['track_name']}</i> {data["status"]}"

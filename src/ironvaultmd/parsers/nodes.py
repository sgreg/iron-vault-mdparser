from typing import Any

from ironvaultmd.parsers.base import NodeParser
from ironvaultmd.util import check_dice, check_ticks, convert_link_name


class AddNodeParser(NodeParser):
    def __init__(self) -> None:
        # add 1 "Tech asset"   or just
        # add 1
        regex = r'^(?P<add>\d+)(?: "(?P<comment>.+)")?$'
        template = '<div class="ivm-add">Add +{{ add }}{{ " " ~ comment if comment }}</div>'
        super().__init__("Add", regex, template)


class BurnNodeParser(NodeParser):
    def __init__(self) -> None:
        # burn from=8 to=2
        regex = r'^from=(?P<from>\d+) to=(?P<to>\d+)$'
        # template = '<div class="ivm-meter ivm-meter-burn"><i>Burn Momentum</i>: {{ from }} &amp;rarr; {{ to }}</div>'
        template = '<div class="ivm-meter ivm-meter-burn"><i>Burn Momentum</i>: {{ from }} &amp;rarr; {{ to }}</div>'
        super().__init__("Burn", regex, template)


class ClockNodeParser(NodeParser):
    def __init__(self) -> None:
        # clock from=2 name="[[Lone Howls\/Clocks\/Titanhold Bounty Hunters closing in on Dykstra.md|Titanhold Bounty Hunters closing in on Dykstra]]" out-of=6 to=3
        # clock name="[[Lone Howls\/Clocks\/Titanhold Bounty Hunters closing in on Dykstra.md|Titanhold Bounty Hunters closing in on Dykstra]]" status="added"

        # Note that https://ironvault.quest/blocks/mechanics-blocks.html#%60clock%60 actually shows a different order.
        # Probably a good idea to capture arbitrary order of parameters in all the node parsers.

        regex = r'^(from=(?P<from>\d+) )?name="\[\[.*\|(?P<name>.*)\]\]" (?(from)out-of=(?P<segments>\d+) to=(?P<filled>\d+)|status="(?P<status>(added|removed|resolved))")$'
        #          ^...................^^                                 ^^^^^^^
        #        make 'from=x ' optional,                        check if 'from' group was actually set,
        #        it's only in clock progresses,                  if so, expect 'out-of' and 'to' here,
        #        but not in clock status changes                 otherwise expect 'status'

        template = '<div class="ivm-clock">{{ text }}</div>'
        super().__init__("Clock", regex, template)

    def create_args(self, data: dict[str, str | Any]) -> dict[str, str | Any]:
        if data["status"] is not None:
            # text = f"<i>Clock</i> {data["status"]}: {data['name']}"
            text = f"Clock {data["status"]}: {data['name']}"
        else:
            # text = f"<i>Clock</i> for {data['name']} -> {data["filled"]} / {data["segments"]}"
            text = f"Clock for {data['name']} -> {data["filled"]} / {data["segments"]}"

        return {"text": text}


class MeterNodeParser(NodeParser):
    def __init__(self) -> None:
        # meter "Momentum" from=5 to=6
        regex = r'^"(?P<meter_name>\w+)" from=(?P<from>\d+) to=(?P<to>\d+$)'
        # template = '<div class="{{ classes }}"><i>{{ meter_name }}</i>: {{ from }} &rarr; {{ to }}</div>'
        template = '<div class="{{ classes }}">{{ meter_name }}: {{ from }} &amp;rarr; {{ to }}</div>'
        super().__init__("Meter", regex, template)

    def create_args(self, data: dict[str, str | Any]) -> dict[str, str | Any]:
        oldval = int(data['from'])
        newval = int(data['to'])

        classes = "ivm-meter"
        if newval > oldval:
            classes += " ivm-meter-increase"
        elif newval < oldval:
            classes += " ivm-meter-decrease"

        return data | {"classes": classes}


class OocNodeParser(NodeParser):
    """iron-vault-mechanics out-of-character notes node parser"""
    def __init__(self) -> None:
        regex = "(?P<data>.*)"
        template = '<div class="ivm-ooc">// {{ data }}</div>'
        super().__init__("OOC", regex, template)


class OracleNodeParser(NodeParser):
    def __init__(self) -> None:
        # oracle name="[Core Oracles \/ Theme](datasworn:oracle_rollable:starforged\/core\/theme)" result="Warning" roll=96
        # oracle name="Will [[Lone Howls\/Clocks\/Clock decrypt Verholm research.md|Clock decrypt Verholm research]] advance? (Likely)" result="No" roll=83
        regex = r'^name="(\[(?P<oracle_name>[^\]]+)\]\(datasworn:.+\)|(?P<oracle_text>[^"]+))" result="(?P<result>[^"]+)" roll=(?P<roll>\d+)$'
        template = '<div class="ivm-oracle">Oracle {{ oracle_name }} rolled a {{ roll }} == {{ result }}</div>'
        super().__init__("Oracle", regex, template)

    def create_args(self, data: dict[str, str | Any]) -> dict[str, str | Any]:
        oracle = "undefined"
        if data["oracle_name"] is not None:
            oracle = convert_link_name(data["oracle_name"])
        elif data["oracle_text"] is not None:
            oracle = convert_link_name(data["oracle_text"])

        return data | {"oracle": oracle}


class PositionNodeParser(NodeParser):
    def __init__(self) -> None:
        #position from="out of combat" to="in control"
        regex = r'^from="(?P<from>.+)" to="(?P<to>.+)"$'
        template = '<div class="{{ classes }}">Position {{ from }} &amp;rarr; {{ to }}</div>'
        super().__init__("Position", regex, template)

    def create_args(self, data: dict[str, str | Any]) -> dict[str, str | Any]:
        classes = "ivm-position"

        match data["to"]:
            case "out of combat":
                classes += " ivm-position-nocombat"
            case "in control":
                classes += " ivm-position-control"
            case "in a bad spot":
                classes += " ivm-position-badspot"

        return data | {"classes": classes}


class ProgressNodeParser(NodeParser):
    def __init__(self) -> None:
        # progress: from=8 name="[[Lone Howls\/Progress\/Connection Dykstra.md|Connection Dykstra]]" rank="dangerous" steps=1
        regex = r'^from=(?P<from>\d+) name="\[\[.*\|(?P<name>.*)\]\]" rank="(?P<rank>\w+)" steps=(?P<steps>\d+)$'
        # template = '<div class="ivm-progress">Progress <i>{{ name }}</i> for {{ rank }}: {{ from }} &amp;rarr; {{ to }}</div>'
        template = '<div class="ivm-progress">Progress {{ name }} for {{ rank }}: {{ from }} &amp;rarr; {{ to }}</div>'
        super().__init__("Progress", regex, template)

    def create_args(self, data: dict[str, str | Any]) -> dict[str, str | Any]:
        ticks, to = check_ticks(data["rank"], int(data["from"]), int(data['steps']))
        return data | {"ticks": ticks, "to": to}


class ProgressRollNodeParser(NodeParser):
    def __init__(self) -> None:
        # progress-roll name="[[Lone Howls\/Progress\/Combat Tayla.md|Combat Tayla]]" score=8 vs1=1 vs2=4
        # Note, before Dec 2024, name parameter may be missing, so pack the whole 'name="[[..|..]]" ' into optional group '(?: ...)?'
        regex = r'^(?:name="\[\[.*\|(?P<name>.*)\]\]" )?score=(?P<score>\d+) vs1=(?P<vs1>\d+) vs2=(?P<vs2>\d+)$'
        super().__init__("Progress Roll", regex, None)

    def create_args(self, data: dict[str, str | Any]) -> dict[str, str | Any]:
        score = int(data["score"])
        vs1 = int(data["vs1"])
        vs2 = int(data["vs2"])

        hitmiss, match = check_dice(score, vs1, vs2)
        extra = {"hitmiss": hitmiss, "match": match}
        return data | extra


class RerollNodeParser(NodeParser):
    def __init__(self) -> None:
        # reroll action="5"
        # reroll vs1="3"
        # reroll vs2="4"
        regex = r'^(?P<dice>action|vs1|vs2)="(?P<value>\d+)"$'
        template = '<div class="ivm-reroll">Reroll {{ dice }} &amp;rarr; {{ value }}</div>'
        super().__init__("Reroll", regex, template)


class RollNodeParser(NodeParser):
    def __init__(self) -> None:
        regex = r'^"(?P<stat_name>\w+)" action=(?P<action>\d+) adds=(?P<adds>\d+) stat=(?P<stat>\d+) vs1=(?P<vs1>\d+) vs2=(?P<vs2>\d+)$'
        super().__init__("Roll", regex, None)

    def create_args(self, data: dict[str, str | Any]) -> dict[str, str | Any]:
        total = min(int(data["action"]) + int(data["stat"]) + int(data["adds"]), 10)
        vs1 = int(data["vs1"])
        vs2 = int(data["vs2"])

        hitmiss, match = check_dice(total, vs1, vs2)

        extra = {"total": total, "hitmiss": hitmiss, "match": match}
        return data | extra


class TrackNodeParser(NodeParser):
    def __init__(self) -> None:
        # track name="[[Lone Howls\/Progress\/Combat Tayla.md|Combat Tayla]]" status="removed"
        regex = r'^name="\[\[.*\|(?P<track_name>.*)\]\]" status="(?P<status>\w+)"$'
        # template = '<div class="ivm-track">Track <i>{{ track_name }}</i> {{ status }}</div>'
        template = '<div class="ivm-track">Track "{{ track_name }}" {{ status }}</div>'
        super().__init__("Track", regex, template)

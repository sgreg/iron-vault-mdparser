"""Concrete node parsers for Iron Vault mechanics.

Each class derives from `NodeParser` and is responsible for parsing a single
mechanics line (e.g., `roll`, `progress-roll`, `burn`, `clock`). Parsers use a
compiled regex to extract named groups and may override `create_args` to
massage values, compute derived fields, or consult the current parsing
`Context` (for example, to perform rolls).
"""

from dataclasses import asdict
from typing import Any

from ironvaultmd.parsers.base import NodeParser
from ironvaultmd.parsers.context import Context
from ironvaultmd.util import check_ticks, convert_link_name, initiative_slugify, position_slugify, ticks_to_progress


class AddNodeParser(NodeParser):
    """Parser for `add` mechanics lines (adds with optional reason)."""
    def __init__(self) -> None:
        # add 1 "Tech asset"   or just
        # add 1
        regex = r'^(?P<add>\d+)(?: "(?P<reason>.+)")?$'
        super().__init__("Add", regex)


class BurnNodeParser(NodeParser):
    """Parser for momentum `burn` lines."""
    def __init__(self) -> None:
        # burn from=8 to=2
        regex = r'^from=(?P<from>\d+) to=(?P<to>\d+)$'
        super().__init__("Burn", regex)

    def create_args(self, data: dict[str, str | Any], ctx: Context) -> dict[str, str | Any]:
        """Apply a momentum burn to the current roll and return updated args.

        Args:
            data: Regex groups including `from` and `to` values.
            ctx: Current parsing context used to access the `RollContext`.

        Returns:
            The original groups merged with the serialized `RollResult`.
        """
        result = ctx.roll.burn(data["from"])
        return data | asdict(result)


class ClockNodeParser(NodeParser):
    """Parser for clock progress or status change lines."""
    def __init__(self) -> None:
        # clock from=2 name="[[Lone Howls\/Clocks\/Titanhold Bounty Hunters closing in on Dykstra.md|Titanhold Bounty Hunters closing in on Dykstra]]" out-of=6 to=3
        # clock name="[[Lone Howls\/Clocks\/Titanhold Bounty Hunters closing in on Dykstra.md|Titanhold Bounty Hunters closing in on Dykstra]]" status="added"

        # Note that https://ironvault.quest/blocks/mechanics-blocks.html#%60clock%60 actually shows a different order.
        # Probably a good idea to capture arbitrary order of parameters in all the node parsers.

        regex = r'^(from=(?P<from>\d+) )?name="\[\[.*\|(?P<name>.*)\]\]" (?(from)out-of=(?P<segments>\d+) to=(?P<to>\d+)|status="(?P<status>(added|removed|resolved))")$'
        #          ^...................^^                                 ^^^^^^^
        #        make 'from=x ' optional,                        check if 'from' group was actually set,
        #        it's only in clock progresses,                  if so, expect 'out-of' and 'to' here,
        #        but not in clock status changes                 otherwise expect 'status'

        super().__init__("Clock", regex)


class ImpactNodeParser(NodeParser):
    """Parser for marking or unmarking character impacts."""
    def __init__(self) -> None:
        # impact "Permanently Harmed" true
        regex = r'^"(?P<impact>[^\"]+)" (?P<marked>(true|false))$'
        super().__init__("Impact", regex)

    def create_args(self, data: dict[str, str | Any], _: Context) -> dict[str, str | Any]:
        """Normalize `marked` from a string to a boolean value.

        Args:
            data: Regex groups including `impact` with the impact's name
                and a string `marked` flag (`"true"` or `"false"`).
            _: Current parsing context (unused).

        Returns:
            The original groups with `marked` converted to a boolean.
        """
        # change 'marked' from string to bool
        data["marked"] = data["marked"] == "true"
        return data


class InitiativeNodeParser(NodeParser):
    """Parser for `initiative` state transitions."""
    def __init__(self) -> None:
        # initiative from="out of combat" to="has initiative"
        regex = r'^from="(?P<from>.+)" to="(?P<to>.+)"$'
        super().__init__("Initiative", regex)

    def create_args(self, data: dict[str, str | Any], _: Context) -> dict[str, str | Any]:
        """Add slugified forms of the initiative states.

        Args:
            data: Regex groups including `from` and `to` state strings.
            _: Current parsing context (unused).

        Returns:
            The original groups merged with `from_slug` and `to_slug` computed
            via `initiative_slugify`.
        """
        return data | {"from_slug": initiative_slugify(data["from"]), "to_slug": initiative_slugify(data["to"])}


class MeterNodeParser(NodeParser):
    """Parser for `meter` changes (e.g., Health, Momentum)."""
    def __init__(self) -> None:
        # meter "Momentum" from=5 to=6
        regex = r'^"(?P<meter_name>[^"]+)" from=(?P<from>\d+) to=(?P<to>\d+$)'
        super().__init__("Meter", regex)

    def create_args(self, data: dict[str, str | Any], _: Context) -> dict[str, str | Any]:
        """Normalize the meter name by removing link decorations and convert values to int.

        Args:
            data: Regex groups including `meter_name`, `from`, and `to`.
            _: Current parsing context (unused).

        Returns:
            The original groups with `meter_name` converted to a plain display
            string and numeric values converted to integers.
        """
        data["meter_name"] = convert_link_name(data["meter_name"])

        data["from"] = int(data["from"])
        data["to"] = int(data["to"])
        diff: int = data["to"] - data["from"]

        return data | {"diff": diff}


class MoveNodeParser(NodeParser):
    """Parser for `move` nodes.

    Note that this only handles standalone `move` lines, not the whole
    `move` block, which is handled in `MoveBlockParser`.
    """
    def __init__(self) -> None:
        # move "[Aid Your Ally](datasworn:move:starforged\/adventure\/aid_your_ally)"
        regex = r'^"\[(?P<move_name>[^]]+)]\((?P<move_link>[^)]+)\)"$'
        super().__init__("Move", regex)

    def create_args(self, data: dict[str, str | Any], _: Context) -> dict[str, str | Any]:
        """Return template args with the move name only.

        Args:
            data: Regex groups including `move_name` and `move_link`.
            _: Current parsing context (unused).

        Returns:
            A minimal dict containing only `name` as the move name.
        """
        return {"name": data["move_name"]}


class OocNodeParser(NodeParser):
    """Parser for out-of-character notes inside mechanics blocks."""
    def __init__(self) -> None:
        regex = r'^"(?P<comment>[^"]*)"$'
        super().__init__("OOC", regex)


class OracleNodeParser(NodeParser):
    """Parser for oracle roll results (text or datasworn references)."""
    def __init__(self) -> None:
        # oracle name="[Core Oracles \/ Theme](datasworn:oracle_rollable:starforged\/core\/theme)" result="Warning" roll=96
        # oracle name="Will [[Lone Howls\/Clocks\/Clock decrypt Verholm research.md|Clock decrypt Verholm research]] advance? (Likely)" result="No" roll=83
        regex = r'^name="(\[(?P<oracle_name>[^\]]+)\]\(datasworn:.+\)|(?P<oracle_text>[^"]+))" result="(?P<result>[^"]+)" roll=(?P<roll>\d+)$'
        super().__init__("Oracle", regex)

    def create_args(self, data: dict[str, str | Any], _: Context) -> dict[str, str | Any]:
        """Derive a normalized oracle name and return extended arguments.

        Args:
            data: Regex groups for `oracle_name` or `oracle_text`, plus
                `result` and `roll`.
            _: Current parsing context (unused).

        Returns:
            The original groups merged with a normalized `oracle` display name
            derived from either `oracle_name` or `oracle_text`.
        """
        oracle = "undefined"
        if data["oracle_name"] is not None:
            oracle = convert_link_name(data["oracle_name"])
        elif data["oracle_text"] is not None:
            oracle = convert_link_name(data["oracle_text"])

        data["result"] = convert_link_name(data["result"])

        return data | {"oracle": oracle}


class PositionNodeParser(NodeParser):
    """Parser for `position` state transitions."""
    def __init__(self) -> None:
        #position from="out of combat" to="in control"
        regex = r'^from="(?P<from>.+)" to="(?P<to>.+)"$'
        super().__init__("Position", regex)

    def create_args(self, data: dict[str, str | Any], _: Context) -> dict[str, str | Any]:
        """Add slugified forms of the position states.

        Args:
            data: Regex groups including `from` and `to` position strings.
            _: Current parsing context (unused).

        Returns:
            The original groups merged with `from_slug` and `to_slug` computed
            via `position_slugify`.
        """
        return data | {"from_slug": position_slugify(data["from"]), "to_slug": position_slugify(data["to"])}


class ProgressNodeParser(NodeParser):
    """Parser for `progress` track changes."""
    def __init__(self) -> None:
        # progress: from=8 name="[[Lone Howls\/Progress\/Connection Dykstra.md|Connection Dykstra]]" rank="dangerous" steps=1
        regex = r'^from=(?P<from>\d+) name="\[\[.*\|(?P<name>.*)\]\]" rank="(?P<rank>\w+)" steps=(?P<steps>\d+)$'
        super().__init__("Progress", regex)

    def create_args(self, data: dict[str, str | Any], _: Context) -> dict[str, str | Any]:
        """Compute and add the new progress state based on rank and progress.

        Rearranges the `data` groups dictionary to contain progress in both
        number of total ticks, and as tuples `(boxes, ticks)`.

        Args:
            data: Regex groups including `rank`, `from`, and `steps`.
            _: Current parsing context (unused).

        Returns:
            The original groups rearranged to contain the old and new progress
            state in both ticks and as tuple `(boxes, ticks)`.
        """
        from_ticks = int(data["from"])
        steps = int(data["steps"])
        ticks, to_ticks = check_ticks(data["rank"], from_ticks, steps)
        from_progress = ticks_to_progress(from_ticks)
        to_progress = ticks_to_progress(to_ticks)

        return {
            "name": data["name"],
            "rank": data["rank"],
            "steps": steps,
            "from": from_progress,
            "to": to_progress,
            "from_ticks": from_ticks,
            "to_ticks": to_ticks,
            "ticks": ticks,
        }


class ProgressRollNodeParser(NodeParser):
    """Parser for `progress-roll` outcomes with optional name."""
    def __init__(self) -> None:
        # progress-roll name="[[Lone Howls\/Progress\/Combat Tayla.md|Combat Tayla]]" score=8 vs1=1 vs2=4
        # Note, before Dec 2024, name parameter may be missing, so pack the whole 'name="[[..|..]]" ' into optional group '(?: ...)?'
        # Addition: in some cases the name might be in the back: progress-roll score=8 vs1=1 vs2=4 name="[[...|...]]"
        regex = r'^(?:name="\[\[.*\|(?P<name_front>.*)\]\]" )?score=(?P<score>\d+) vs1=(?P<vs1>\d+) vs2=(?P<vs2>\d+)(?: name="\[\[.*\|(?P<name_back>.*)\]\]")?$'
        super().__init__("Progress Roll", regex)

    def create_args(self, data: dict[str, str | Any], ctx: Context) -> dict[str, str | Any]:
        """Perform the progress roll via context and set the track name.

        The track name might be either in the beginning or the end of the
        node parameters, possibly even missing altogether depending on the
        used Iron-Vault version. Tries to find the name on both sides and
        otherwise sets it to `"undefined"`.

        Args:
            data: Regex groups including `score`, `vs1`, `vs2`, and an optional
                progress `name` (captured as `name_front` or `name_back`).
            ctx: Current parsing context used to access the `RollContext`.

        Returns:
            The original groups plus a normalized `name` and the serialized
            `RollResult` (score, dice, hit/miss, match flags).
        """
        name = data["name_front"]
        if name is None:
            name = data["name_back"]
        if name is None:
            name = "undefined"

        data["name"] = name

        result = ctx.roll.progress_roll(data["score"], data["vs1"], data["vs2"])
        return data | asdict(result)


class RerollNodeParser(NodeParser):
    """Parser for a selective die `reroll`."""
    def __init__(self) -> None:
        # reroll action="5"
        # reroll vs1="3"
        # reroll vs2="4"
        regex = r'^(?P<die>action|vs1|vs2)="(?P<value>\d+)"$'
        super().__init__("Reroll", regex)

    def create_args(self, data: dict[str, str | Any], ctx: Context) -> dict[str, str | Any]:
        """Apply a selective reroll using the context and return new values.

        Args:
            data: Regex groups including which `die` to reroll (`action`,
                `vs1`, or `vs2`) and the new `value`.
            ctx: Current parsing context used to access the `RollContext`.

        Returns:
            The original groups merged with the replaced die's initial value,
            and serialized `RollResult` after applying the reroll.
        """
        data["value"] = int(data["value"])
        current = ctx.roll.value(data["die"])
        result = ctx.roll.reroll(data["die"], data["value"])
        return data | {"old_value": current} | asdict(result)


class RollNodeParser(NodeParser):
    """Parser for a standard roll including adds and stat."""
    def __init__(self) -> None:
        regex = r'^"(?P<stat_name>\w+)" action=(?P<action>\d+) adds=(?P<adds>\d+) stat=(?P<stat>\d+) vs1=(?P<vs1>\d+) vs2=(?P<vs2>\d+)$'
        super().__init__("Roll", regex)

    def create_args(self, data: dict[str, str | Any], ctx: Context) -> dict[str, str | Any]:
        """Perform the roll and return extended arguments.

        Args:
            data: Regex groups including `stat_name`, `action`, `adds`, `stat`,
                `vs1`, and `vs2`.
            ctx: Current parsing context used to access the `RollContext`.

        Returns:
            The original groups merged with the serialized `RollResult`.
        """
        result = ctx.roll.roll(data["action"], data["stat"], data["adds"], data["vs1"], data["vs2"])
        return data | asdict(result)


class TrackNodeParser(NodeParser):
    """Parser for `track` status changes (added/removed/resolved)."""
    def __init__(self) -> None:
        # track name="[[Lone Howls\/Progress\/Combat Tayla.md|Combat Tayla]]" status="removed"

        # XXX this should have similar content than the clock node, double-check that
        # see https://ironvault.quest/blocks/mechanics-blocks.html#%60track%60
        regex = r'^name="\[\[.*\|(?P<track_name>.*)\]\]" status="(?P<status>\w+)"$'
        super().__init__("Track", regex)


class XpNodeParser(NodeParser):
    """Parser for `xp` value changes."""
    def __init__(self) -> None:
        # xp from=3 to=5
        regex = r'^from=(?P<from>\d+) to=(?P<to>\d+)$'
        super().__init__("XP", regex)

    def create_args(self, data: dict[str, str | Any], _: Context) -> dict[str, str | Any]:
        """Compute the difference between `to` and `from` for convenience.

        Args:
            data: Regex groups including `from` and `to` XP values.
            _: Current parsing context (unused).

        Returns:
            The original groups converted to integer values and with its `diff` value.
        """
        data["from"] = int(data["from"])
        data["to"] = int(data["to"])
        diff: int = data["to"] - data["from"]

        return data | {"diff": diff}

"""Concrete node parsers for Iron Vault mechanics.

Each class derives from either `NodeParser` or `ParameterNodeParser` and is
responsible for parsing a single mechanics node line (e.g., `roll`,
`progress-roll`, `burn`, `clock`).

Parsers use a compiled regex to extract named groups and may override
`handle_args` to adjust values, compute derived fields, or consult the
current parsing `Context` (for example, to perform rolls).

Classes derived from `NodeParser` use a strict, fixed parameter-based regex,
while classes derived from `ParameterNodeParser` use a more relaxed key=value
of arbitrary order regex.
"""

from dataclasses import asdict
from typing import Any

from ironvaultmd.parsers.base import NodeParser, ParameterNodeParser
from ironvaultmd.parsers.context import Context, NameCollection
from ironvaultmd.util import (
    check_ticks,
    convert_link_name,
    initiative_slugify,
    position_slugify,
    ticks_to_progress,
    ticks_to_float,
)


class AddNodeParser(NodeParser):
    """Parser for `add` mechanics lines (adds with optional reason)."""

    def __init__(self) -> None:
        # add 1 "Tech asset"   or just
        # add 1
        regex = r'^(?P<add>\d+)(?: "(?P<reason>.+)")?$'
        super().__init__(NameCollection("Add", "add", "add"), regex)

        # XXX should args be converted to ints?


class BurnNodeParser(NodeParser):
    """Parser for momentum `burn` lines."""

    def __init__(self) -> None:
        # burn from=8 to=2
        regex = r"^from=(?P<from>\d+) to=(?P<to>\d+)$"
        super().__init__(NameCollection("Burn", "burn", "burn"), regex)

    def handle_args(self, data: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Apply a momentum burn to the current roll and return updated args.

        Args:
            data: Regex groups including `from` and `to` values.
            ctx: Current parsing context used to access the `RollContext`.

        Returns:
            The original groups merged with the serialized `RollResult`.
        """
        result = ctx.roll.burn(data["from"])
        return data | asdict(result)


class ClockNodeParser(ParameterNodeParser):
    """Parser for clock progress or status change lines."""

    def __init__(self) -> None:
        # clock from=2 name="[[Lone Howls\/Clocks\/Titanhold Bounty Hunters closing in on Dykstra.md|Titanhold Bounty Hunters closing in on Dykstra]]" out-of=6 to=3
        # clock name="[[Lone Howls\/Clocks\/Titanhold Bounty Hunters closing in on Dykstra.md|Titanhold Bounty Hunters closing in on Dykstra]]" status="added"
        keys = ["name", "from", "to", "out-of", "status"]
        super().__init__(NameCollection("Clock", "clock", "clock"), keys)

    def handle_args(self, data: dict[str, Any], _: Context) -> dict[str, Any]:
        data["name"] = convert_link_name(data.get("name", "unknown"))
        data["segments"] = data.get("out-of", 0)
        return data

        # XXX there's always "segments" even if "out-of" is missing, should it be changed?


class ImpactNodeParser(NodeParser):
    """Parser for marking or unmarking character impacts."""

    def __init__(self) -> None:
        # impact "Permanently Harmed" true
        regex = r'^"(?P<impact>[^\"]+)" (?P<marked>(true|false))$'
        super().__init__(NameCollection("Impact", "impact", "impact"), regex)

    def handle_args(self, data: dict[str, Any], _: Context) -> dict[str, Any]:
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
        super().__init__(
            NameCollection("Initiative", "initiative", "initiative"), regex
        )

    def handle_args(self, data: dict[str, Any], _: Context) -> dict[str, Any]:
        """Add slugified forms of the initiative states.

        Args:
            data: Regex groups including `from` and `to` state strings.
            _: Current parsing context (unused).

        Returns:
            The original groups merged with `from_slug` and `to_slug` computed
            via `initiative_slugify`.
        """
        return data | {
            "from_slug": initiative_slugify(data["from"]),
            "to_slug": initiative_slugify(data["to"]),
        }


class MeterNodeParser(NodeParser):
    """Parser for `meter` changes (e.g., Health, Momentum)."""

    def __init__(self) -> None:
        # meter "Momentum" from=5 to=6
        regex = r'^"(?P<meter_name>[^"]+)" from=(?P<from>\d+) to=(?P<to>\d+$)'
        super().__init__(NameCollection("Meter", "meter", "meter"), regex)

    def handle_args(self, data: dict[str, Any], _: Context) -> dict[str, Any]:
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
        super().__init__(NameCollection("Move", "move", "move"), regex)

    def handle_args(self, data: dict[str, Any], _: Context) -> dict[str, Any]:
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
        regex = '^"(?P<comment>.*)"$'
        super().__init__(NameCollection("OOC", "-", "ooc"), regex)

    def handle_args(self, data: dict[str, Any], _: Context) -> dict[str, Any]:
        """Return template args replacing escaping from double quotes.

        Args:
            data: Regex group including `comment`.
            _: Current parsing context (unused).

        Returns:
            The original dictionary with unescaped double quotes.

        """
        data["comment"] = str(data.get("comment", "")).replace('\\"', '"')
        return data


class OracleNodeParser(ParameterNodeParser):
    """Parser for oracle roll results (text or datasworn references)."""

    def __init__(self) -> None:
        # oracle name="[Core Oracles \/ Theme](datasworn:oracle_rollable:starforged\/core\/theme)" result="Warning" roll=96
        # oracle name="Will [[Lone Howls\/Clocks\/Clock decrypt Verholm research.md|Clock decrypt Verholm research]] advance? (Likely)" result="No" roll=83
        known_keys = ["name", "result", "roll", "cursed", "replaced"]
        super().__init__(NameCollection("Oracle", "oracle", "oracle"), known_keys)

    def handle_args(self, data: dict[str, Any], _: Context) -> dict[str, Any]:
        data["oracle"] = convert_link_name(data.get("name", "unknown"))
        data["result"] = convert_link_name(data.get("result", "unknown"))

        return data

        # XXX this keeps the "name" entry, kinda no point for that?


class PositionNodeParser(NodeParser):
    """Parser for `position` state transitions."""

    def __init__(self) -> None:
        # position from="out of combat" to="in control"
        regex = r'^from="(?P<from>.+)" to="(?P<to>.+)"$'
        super().__init__(NameCollection("Position", "position", "position"), regex)

    def handle_args(self, data: dict[str, Any], _: Context) -> dict[str, Any]:
        """Add slugified forms of the position states.

        Args:
            data: Regex groups including `from` and `to` position strings.
            _: Current parsing context (unused).

        Returns:
            The original groups merged with `from_slug` and `to_slug` computed
            via `position_slugify`.
        """
        return data | {
            "from_slug": position_slugify(data["from"]),
            "to_slug": position_slugify(data["to"]),
        }


class ProgressNodeParser(ParameterNodeParser):
    """Parser for `progress` track changes."""

    def __init__(self) -> None:
        # progress: from=8 name="[[Lone Howls\/Progress\/Connection Dykstra.md|Connection Dykstra]]" rank="dangerous" steps=1
        # regex = r'^from=(?P<from>\d+) name="\[\[.*\|(?P<name>.*)\]\]" rank="(?P<rank>\w+)" steps=(?P<steps>\d+)$'
        keys = ["from", "name", "rank", "steps"]
        super().__init__(NameCollection("Progress", "progress", "progress"), keys)

    def handle_args(self, data: dict[str, Any], _: Context) -> dict[str, Any]:
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
        from_ticks = data.get("from", 0)
        steps = data.get("steps", 0)
        ticks, to_ticks = check_ticks(data.get("rank", "unknown"), from_ticks, steps)

        return {
            "name": convert_link_name(data.get("name", "undefined")),
            "rank": data.get("rank", "unknown"),
            "steps": steps,
            "from": ticks_to_progress(from_ticks),
            "to": ticks_to_progress(to_ticks),
            "from_ticks": from_ticks,
            "to_ticks": to_ticks,
            "from_fract": ticks_to_float(from_ticks),
            "to_fract": ticks_to_float(to_ticks),
            "ticks": ticks,
            "extra": data["extra"],
        }


class ProgressRollNodeParser(ParameterNodeParser):
    """Parser for `progress-roll` outcomes with optional name."""

    def __init__(self) -> None:
        # progress-roll name="[[Lone Howls\/Progress\/Combat Tayla.md|Combat Tayla]]" score=8 vs1=1 vs2=4
        # Note, before Dec 2024, name parameter may be missing, so pack the whole 'name="[[..|..]]" ' into optional group '(?: ...)?'
        # Addition: in some cases the name might be in the back: progress-roll score=8 vs1=1 vs2=4 name="[[...|...]]"
        keys = ["name", "score", "vs1", "vs2"]
        super().__init__(
            NameCollection("Progress Roll", "progress-roll", "progress_roll"), keys
        )

    def handle_args(self, data: dict[str, Any], ctx: Context) -> dict[str, Any]:
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
        data["name"] = convert_link_name(data.get("name", "undefined"))
        result = ctx.roll.progress_roll(data["score"], data["vs1"], data["vs2"])
        return data | asdict(result)


class RerollNodeParser(NodeParser):
    """Parser for a selective die `reroll`."""

    def __init__(self) -> None:
        # reroll action="5"
        # reroll vs1="3"
        # reroll vs2="4"
        regex = r'^(?P<die>action|vs1|vs2)="(?P<value>\d+)"$'
        super().__init__(NameCollection("Reroll", "reroll", "reroll"), regex)

    def handle_args(self, data: dict[str, Any], ctx: Context) -> dict[str, Any]:
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
        super().__init__(NameCollection("Roll", "roll", "roll"), regex)

    def handle_args(self, data: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Perform the roll and return extended arguments.

        Args:
            data: Regex groups including `stat_name`, `action`, `adds`, `stat`,
                `vs1`, and `vs2`.
            ctx: Current parsing context used to access the `RollContext`.

        Returns:
            The original groups merged with the serialized `RollResult`.
        """
        result = ctx.roll.roll(
            data["stat_name"],
            data["action"],
            data["stat"],
            data["adds"],
            data["vs1"],
            data["vs2"],
        )
        return data | asdict(result)

        # XXX there's some values ints (vs1, vs2), others strings (action, adds, stat, score)


class RollsNodeParser(NodeParser):
    """Parser for `rolls` used inside dice-expr blocks"""

    def __init__(self) -> None:
        # rolls 1 2 3 dice="3d6"
        # rolls 1 dice="1d4"
        regex = r'(?P<rolls>((\d+) ?)+) dice="(?P<dice>[0-9]+d[0-9]+)"'
        super().__init__(NameCollection("Rolls", "rolls", "rolls"), regex)

    def handle_args(self, data: dict[str, Any], _: Context) -> dict[str, Any]:
        data["rolls_array"] = [int(roll) for roll in data["rolls"].split(" ")]
        return data


class TrackNodeParser(ParameterNodeParser):
    """Parser for `track` status changes (added/removed/resolved)."""

    def __init__(self) -> None:
        # track name="[[Lone Howls\/Progress\/Combat Tayla.md|Combat Tayla]]" status="removed"
        keys = ["name", "status"]
        super().__init__(NameCollection("Track", "track", "track"), keys)

    def handle_args(self, data: dict[str, Any], _: Context) -> dict[str, Any]:
        data["name"] = convert_link_name(data.get("name", "undefined"))
        return data


class XpNodeParser(NodeParser):
    """Parser for `xp` value changes."""

    def __init__(self) -> None:
        # xp from=3 to=5
        regex = r"^from=(?P<from>\d+) to=(?P<to>\d+)$"
        super().__init__(NameCollection("XP", "xp", "xp"), regex)

    def handle_args(self, data: dict[str, Any], _: Context) -> dict[str, Any]:
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

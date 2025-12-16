"""Block parsers for Iron Vault mechanics.

This module implements concrete `MechanicsBlockParser` subclasses that handle
high-level mechanics constructs:

- `ActorBlockParser`: Creates an actor container with a rendered name.
- `MoveBlockParser`: Creates a move container and, on finalize, decorates it
  based on the computed roll result.
- `OracleGroupBlockParser` and `OracleBlockParser`: Render oracle-related sections.
- `OraclePromptBlockParser`: Renders narrative oracle prompts.

Parsers rely on helpers from `ironvaultmd.util` and optional Jinja templates
provided via `ironvaultmd.parsers.templater`.
"""

import logging
from typing import Any

from ironvaultmd import logger_name
from ironvaultmd.parsers.base import MechanicsBlockParser
from ironvaultmd.util import convert_link_name

logger = logging.getLogger(logger_name)


class ActorBlockParser(MechanicsBlockParser):
    """Block parser for mechanics actor sections.

    Matches an opening line that references an Obsidian link with a piped
    label and renders the label as the actor name.
    """
    def __init__(self):
        """Initialize the parser with its regex pattern."""
        regex = r'^name="\[\[.*\|(?P<name>.*)\]\]"$'
        super().__init__("Actor", regex)


class MoveBlockParser(MechanicsBlockParser):
    """Block parser for mechanics move sections.

    Creates a move container and, upon finalization, updates CSS classes
    based on the move roll outcome's hit/miss and match status.
    """
    def __init__(self):
        """Initialize the parser with its regex pattern."""
        regex = r'"\[(?P<name>[^]]+)]\((?P<link>[^)]+)\)"'
        super().__init__("Move", regex)

    def finalize(self, ctx):
        """Style the move block based on its roll outcome if a roll occurred.

        The outcome is based on the `RollResult` within the `Context` and
        takes possible dice rerolls and momentum burning into account.

        Args:
            ctx: Current parsing context.
        """
        if not ctx.roll.rolled:
            logger.debug("No roll context, skipping")
            return

        result = ctx.roll.get()

        # Style the main move block <div> with classes based on the roll result
        class_hitmiss = f"ivm-move-result-{result.hitmiss}"
        class_match = "ivm-move-result-match" if result.match else ""
        current_classes = ctx.parent.get("class", "")

        new_classes = " ".join(c for c in [current_classes, class_hitmiss, class_match] if c)
        ctx.parent.set("class", new_classes)


class OracleGroupBlockParser(MechanicsBlockParser):
    """Block parser for an oracle group header."""
    def __init__(self):
        """Initialize the parser with its regex pattern."""
        regex = r'^name="(?P<oracle>[^"]*)"$'
        super().__init__("Oracle Group", regex, "oracle")


class OracleBlockParser(MechanicsBlockParser):
    """Block parser for a single oracle roll result."""
    def __init__(self):
        # See the oracle node parser, there can be two types (that I know of so far):
        # oracle name="[Core Oracles \/ Theme](datasworn:oracle_rollable:starforged\/core\/theme)" result="Warning" roll=96
        # oracle name="Will [[Lone Howls\/Clocks\/Clock decrypt Verholm research.md|Clock decrypt Verholm research]] advance? (Likely)" result="No" roll=83
        regex = r'^name="(\[(?P<oracle_name>[^\]]+)\]\(datasworn:.+\)|(?P<oracle_text>[^"]+))" result="(?P<result>[^"]+)" roll=(?P<roll>\d+)$'
        super().__init__("Oracle", regex)

    def create_args(self, data: dict[str, str | Any]) -> dict[str, str | Any]:
        # This is also taken straight from the oracle node parser.
        # Should probably combine those to some common place?
        oracle = "undefined"
        if data["oracle_name"] is not None:
            oracle = convert_link_name(data["oracle_name"])
        elif data["oracle_text"] is not None:
            oracle = convert_link_name(data["oracle_text"])

        data["result"] = convert_link_name(data["result"])

        return data | {"oracle": oracle}


class OraclePromptBlockParser(MechanicsBlockParser):
    """Block parser for oracle prompts (narrative lines)."""
    def __init__(self):
        """Initialize the parser with its regex pattern."""
        regex = r'^"(?P<prompt>[^"]*)"$'
        super().__init__("Oracle Prompt", regex, "oracle")

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
import xml.etree.ElementTree as etree
from dataclasses import asdict
from typing import Any

from ironvaultmd import logger_name
from ironvaultmd.parsers.base import MechanicsBlockParser
from ironvaultmd.parsers.context import Context, BlockContext
from ironvaultmd.parsers.templater import get_templater
from ironvaultmd.util import convert_link_name

logger = logging.getLogger(logger_name)


class ActorBlockParser(MechanicsBlockParser):
    """Block parser for mechanics actor sections.

    Matches an opening line that references an Obsidian link with a piped
    label and renders the label as the actor name.
    """
    def __init__(self) -> None:
        """Initialize the parser with its regex pattern."""
        name = BlockContext.Names("Actor", "actor", "actor")
        regex = r'^name="\[\[.*\|(?P<name>.*)\]\]"$'
        super().__init__(name, regex)


class MoveBlockParser(MechanicsBlockParser):
    """Block parser for mechanics move sections.

    Creates a move container and, upon finalization, updates CSS classes
    based on the move roll outcome's hit/miss and match status.
    """
    def __init__(self) -> None:
        """Initialize the parser with its regex pattern."""
        name = BlockContext.Names("Move", "move", "move")
        regex = r'"\[(?P<name>[^]]+)]\((?P<link>[^)]+)\)"'
        super().__init__(name, regex)

    def finalize_nodes(self, ctx: Context) -> None:
        """Add the move's roll outcome as a dedicated node.

        If the `rolled` flag isn't set in the attached `RollContext`,
        or no `roll-result` template is found, nothing happens.

        Args:
            ctx: Current parsing `Context`.
        """
        if ctx.roll.rolled:
            template = get_templater().get_template("roll_result", "nodes")
            if template is not None:
                element = etree.fromstring(template.render(asdict(ctx.roll.get())))
                ctx.parent.append(element)

    def finalize_args(self, ctx: Context) -> dict[str, Any]:
        """Add the move's roll outcome to the args.

        The outcome is based on the `RollResult` within the `Context` and
        takes possible dice rerolls and momentum burning into account.

        Args:
            ctx: Current parsing `Context`.

        Returns:
            Args dictionary with the roll outcome information added.
        """
        return ctx.args | {"rolled": ctx.roll.rolled} | asdict(ctx.roll.get())


class OracleGroupBlockParser(MechanicsBlockParser):
    """Block parser for an oracle group header."""
    def __init__(self) -> None:
        """Initialize the parser with its regex pattern."""
        name = BlockContext.Names("Oracle Group", "oracle-group", "oracle")
        regex = r'^name="(?P<oracle>[^"]*)"$'
        super().__init__(name, regex)


class OracleBlockParser(MechanicsBlockParser):
    """Block parser for a single oracle roll result."""
    def __init__(self) -> None:
        name = BlockContext.Names("Oracle", "oracle", "oracle")
        # See the oracle node parser, there can be two types (that I know of so far):
        # oracle name="[Core Oracles \/ Theme](datasworn:oracle_rollable:starforged\/core\/theme)" result="Warning" roll=96
        # oracle name="Will [[Lone Howls\/Clocks\/Clock decrypt Verholm research.md|Clock decrypt Verholm research]] advance? (Likely)" result="No" roll=83
        regex = r'^name="(\[(?P<oracle_name>[^\]]+)\]\(datasworn:.+\)|(?P<oracle_text>[^"]+))" result="(?P<result>[^"]+)" roll=(?P<roll>\d+)$'
        super().__init__(name, regex)

    def handle_args(self, data: dict[str, Any], _: Context) -> dict[str, Any]:
        # This is also taken straight from the oracle node parser.
        # Should probably combine those to some common place?
        oracle_raw = data.get("oracle_name") or data.get("oracle_text")
        oracle = convert_link_name(oracle_raw) if oracle_raw else "undefined"

        data["result"] = convert_link_name(data["result"])

        return data | {"oracle": oracle}


class OraclePromptBlockParser(MechanicsBlockParser):
    """Block parser for oracle prompts (narrative lines)."""
    def __init__(self) -> None:
        """Initialize the parser with its regex pattern."""
        name = BlockContext.Names("Oracle Prompt", "-", "oracle")
        regex = r'^"(?P<prompt>[^"]*)"$'
        super().__init__(name, regex)

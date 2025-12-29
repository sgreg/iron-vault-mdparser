"""Parsing context and roll state for mechanics blocks.

This module defines small helper classes that carry state while parsing
`iron-vault-mechanics` sections:

- `NameCollection`: Contextual names for logging and parser / template lookup.
- `RollResult`: A lightweight value object representing the outcome of a roll.
- `RollContext`: Mutable roll state capable of performing move and progress rolls,
  momentum-burn adjustments, as well as selective rerolls.
- `BlockContext`: Container for a named mechanics block with its root element
  and associated `RollContext`.
- `Context`: A stack-based context that manages nested blocks and exposes the
  current parent element and roll context.
"""

import logging
import xml.etree.ElementTree as etree
from dataclasses import dataclass, field
from typing import Any

from ironvaultmd import logger_name
from ironvaultmd.parsers.templater import get_templater
from ironvaultmd.util import check_dice

logger = logging.getLogger(logger_name)


@dataclass
class NameCollection:
    """Represents the names used for parsing context.

    Different use cases require different versions of the name,
    such as displaying the name of a block or node itself (`name`),
    the lookup key name of the block or node parser (`parser`),
    and the parser's associated template key name (`template`).

    Attributes:
        name: Display name, e.g., "Oracle Group", "Progress Roll".
        parser: Parser lookup name, e.g., "oracle-group", "progress-roll".
        template: Template lookup name, e.g., "oracle_group", "progress_roll".
    """
    name: str
    parser: str | None = None
    template: str | None = None


@dataclass
class RollResult:
    """Outcome of a mechanics roll.

    Attributes:
        score: Final result used for comparison (action+stat+adds capped at 10
            for rolls, progress value, or amount of burned momentum)
        vs1: First challenge die value.
        vs2: Second challenge die value.
        hitmiss: Outcome string (`miss`, `hit`, or `strong`)
        match: Whether the roll was a match or not.
    """
    score: int
    vs1: int
    vs2: int
    hitmiss: str
    match: bool


class RollContext:
    """Mutable context to compute and track roll outcomes.

    Supports three roll modes:
    - Normal action roll via `roll()`.
    - Progress-based roll via `progress_roll()`.
    - Momentum burn via `burn()` modifying the most recent action roll.

    Methods return a `RollResult` snapshot and update the internal state so
    that later operations (e.g., `finalize()` in `MoveBlockParser`) can style
    output accordingly.
    """
    action: int
    stat: int
    adds: int
    vs1: int
    vs2: int
    momentum: int
    progress: int
    rolled: bool

    def __init__(self) -> None:
        """Create a fresh roll context with zeroed values."""
        self.action = 0
        self.stat = 0
        self.adds = 0
        self.vs1 = 0
        self.vs2 = 0
        self.momentum = 0
        self.progress = 0
        self.rolled = False

    def roll(self, action: int | str, stat: int | str, adds: int | str, vs1: int | str, vs2: int | str) -> RollResult:
        """Perform a standard action roll.

        Args:
            action: Action die value.
            stat: Stat value rolled with.
            adds: Additional modifiers.
            vs1: First challenge die value.
            vs2: Second challenge die value.

        Returns:
            The computed `RollResult`.

        Notes:
            Overwrites any existing roll state with the new result.
        """
        if self.rolled:
            logger.warning("RollContext roll with existing roll data")

        self.action = int(action)
        self.stat = int(stat)
        self.adds = int(adds)
        self.vs1 = int(vs1)
        self.vs2 = int(vs2)
        self.rolled = True

        return self.get()

    def progress_roll(self, progress: int | str, vs1: int | str, vs2: int | str) -> RollResult:
        """Perform a progress roll.

        Args:
            progress: Progress score to compare against challenge dice.
            vs1: First challenge die value.
            vs2: Second challenge die value.

        Returns:
            The computed `RollResult`.

        Notes:
            Overwrites any existing roll state with a progress-based result.
        """
        if self.rolled:
            logger.warning("RollContext progress-roll with existing roll data")

        self.progress = int(progress)
        self.vs1 = int(vs1)
        self.vs2 = int(vs2)
        self.rolled = True

        return self.get()

    def reroll(self, die: str, value: int | str) -> RollResult:
        """Reroll a single die value in the current roll state.

        Args:
            die: Which die to reroll: `action`, `vs1`, or `vs2`.
            value: New value for the specified die.

        Returns:
            The updated `RollResult`.

        Notes:
            Rerolling the action die has no effect for progress rolls and will
            emit a warning.
        """
        if not self.rolled:
            logger.warning("RollContext reroll without existing roll data")

        if die == "action":
            if self.progress > 0:
                logger.warning("Attempting to reroll action die on progress roll, ignoring")
            else:
                self.action = int(value)
        elif die == "vs1":
            self.vs1 = int(value)
        elif die == "vs2":
            self.vs2 = int(value)
        else:
            logger.warning(f"Unhandled reroll die: {die}")

        return self.get()

    def burn(self, value: int | str) -> RollResult:
        """Burn momentum for the current action roll.

        Args:
            value: Momentum value to burn, replacing the computed score.

        Returns:
            The updated `RollResult` reflecting the burned momentum.

        Notes:
            Momentum cannot be burned for progress rolls; a warning is logged
            and the request is ignored in that case.
        """
        if not self.rolled:
            logger.warning("RollContext momentum burn without existing roll data")

        if self.progress > 0:
            logger.warning("Attempting to burn momentum for progress roll, ignoring")
        else:
            self.momentum = int(value)

        return self.get()

    def get(self) -> RollResult:
        """Compute and return the current roll result snapshot.

        Returns:
            A `RollResult` with the current score, challenge dice, and outcome flags.
        """
        if self.progress > 0:
            score = self.progress
        elif self.momentum > 0:
            score = self.momentum
        else:
            score = min(self.action + self.stat + self.adds, 10)

        hitmiss, match = check_dice(score, self.vs1, self.vs2)
        return RollResult(score, self.vs1, self.vs2, hitmiss, match)

    def value(self, attribute: str) -> int | bool | None:
        """Retrieves the value of the specified attribute if it exists.

        Args:
            attribute: The name of the attribute to retrieve.

        Returns:
            The value of the requested attribute, if it exists, `None` otherwise.
        """
        return getattr(self, attribute, None)


@dataclass
class BlockContext:
    """Container for a named mechanics block and its roll context.

    Attributes:
        names: Names of the current mechanics block parser (e.g., `move`).
        root: Root HTML element of the block in the output tree.
        matches: Named regex groups the parser matched, or `None`.
        args: Dictionary of parsed arguments.
        roll: `RollContext` attached to the block to accumulate roll data.
    """

    names: NameCollection
    root: etree.Element
    matches: dict[str, Any] | None
    args: dict[str, Any]
    roll: RollContext = field(default_factory=RollContext)


class Context:
    """Stack-based parsing context for mechanics block content.

    Manages an element stack via `push`/`pop` and exposes convenience
    properties for the current parent, block names, and roll context.

    Attributes:
        root: The outermost iron-vault-mechanics block `<div>`.
        blocks: Internal stack of `BlockContext` instances, handling all
            nodes and blocks contained within the main mechanics block.
        root_names: `NameCollection` values for the root element.
    """
    root_names = NameCollection("root")

    def __init__(self, root: etree.Element) -> None:
        """Initialize a new Context.

        Creates the main mechanics block `<div>` for the currently parsed
        iron-vault-mechanics Markdown block and appends it as a child to
        the given `root` element.

        Every `IronVaultMechanicsBlockProcessor.run()` call creates its
        own `Context` to hold and process all the data within the parsed
        iron-vault-mechanics block.

        Args:
            root: Root HTML element the mechanics block `<div>` is appended to
        """
        template = get_templater().get_default_template("mechanics")
        mechanics_block = etree.fromstring(template.render())
        root.append(mechanics_block)

        self.root = mechanics_block
        self.blocks: list[BlockContext] = []

    @property
    def parent(self) -> etree.Element:
        """Return the current parent element for new output nodes."""
        return self.blocks[-1].root if self.blocks else self.root

    @property
    def names(self) -> NameCollection:
        """Return the names of the current block or `root` if none is active."""
        return self.blocks[-1].names if self.blocks else self.root_names

    @property
    def matches(self) -> dict[str, Any] | None:
        """Return the matches dictionary of the current block, if any."""
        return self.blocks[-1].matches if self.blocks else None

    @property
    def args(self) -> dict[str, Any] | None:
        """Return the args dictionary of the current block, if any."""
        return self.blocks[-1].args if self.blocks else None

    @property
    def roll(self) -> RollContext | None:
        """Return the roll context for the current block, if any."""
        return self.blocks[-1].roll if self.blocks else None

    def push(self, block: BlockContext) -> None:
        """Push a new `BlockContext` onto the context stack.

        Args:
            block: New `BlockContext`

        Returns:
            Nothing.
        """
        self.blocks.append(block)
        logger.debug(f"CONTEXT: pushing #{len(self.blocks)} {repr(block)}  str {str(block)}")

    def pop(self) -> None:
        """Pop the current block from the context stack.

        Notes:
            Logs a warning when called on an empty stack and does nothing.
        """
        if not self.blocks:
            logger.warning("pop() called on empty stack, ignoring")
            return
        logger.debug(f"CONTEXT: popping #{len(self.blocks)} -> #{len(self.blocks) - 1}")
        self.blocks.pop()

    def replace_root(self, new_root: etree.Element) -> None:
        """Replace the current block's root element with a new one.

        Block parsers use a temporary placeholder `<div>` during parsing
        and only render the actual template in the `finalize()` step.
        This way, the `MoveBlockParser` can style its container element
        based on roll results nodes within the block.

        The placeholder `<div>` is held in the block's `root` attribute.
        This method copies all child elements from there into the given
        `new_root` element and replaces the placeholder with it in both
        the stack hierarchy (i.e., the block's parent) and within the
        block itself.

        Args:
            new_root: A `<div>` container that will become the currently
                active's block new root element

        Returns:
            Nothing.
        """
        if not self.blocks:
            logger.warning("Attempting to replace mechanics block root, ignoring")
            return

        block = self.blocks[-1]
        parent = self.blocks[-2].root if len(self.blocks) > 1 else self.root

        # Get all child elements within the block's root element
        elements = block.root.findall("*")
        # Copy them into the new_root element
        for element in elements:
            new_root.append(element)

        # Replace the root element in the stack hierarchy
        # by adjusting the block's parent's list of children
        parent.remove(block.root)
        parent.append(new_root)

        # Set the block's own root element to the new one
        block.root = new_root

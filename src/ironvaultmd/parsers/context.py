"""Parsing context and roll state for mechanics blocks.

This module defines small helper classes that carry state while parsing
`iron-vault-mechanics` sections:

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
from dataclasses import dataclass

from ironvaultmd import logger_name
from ironvaultmd.util import check_dice

logger = logging.getLogger(logger_name)


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
    def __init__(self):
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


class BlockContext:
    """Container for a named mechanics block and its roll context.

    Attributes:
        name: Name of the current mechanics block (e.g., `move`).
        root: Root HTML element of the block in the output tree.
        roll: `RollContext` attached to the block to accumulate roll data.
    """
    def __init__(self, name: str, root: etree.Element):
        self.name = name
        self.root = root
        self.roll = RollContext()


class Context:
    """Stack-based parsing context for mechanics content.

    Manages an element stack via `push`/`pop` and exposes convenience
    properties for the current parent, block name, and roll context.

    Attributes:
        root: The outermost root HTML element that contains mechanics output.
        blocks: Internal stack of `BlockContext` instances.
    """
    def __init__(self, root: etree.Element):
        self.root = root
        self.blocks: list[BlockContext] = []

    @property
    def parent(self) -> etree.Element:
        """Return the current parent element for new output nodes."""
        if len(self.blocks) > 0:
            return self.blocks[-1].root
        return self.root

    @property
    def name(self) -> str:
        """Return the name of the current block or `root` if none is active."""
        if len(self.blocks) == 0:
            return "root"
        return self.blocks[-1].name

    @property
    def roll(self) -> RollContext | None:
        """Return the roll context for the current block, if any."""
        if len(self.blocks) == 0:
            return None
        return self.blocks[-1].roll

    def push(self, name: str, element: etree.Element) -> None:
        """Push a new block onto the context stack.

        Args:
            name: Name of the mechanics block being entered.
            element: Root HTML element for the block.
        """
        block = BlockContext(name, element)
        self.blocks.append(block)
        logger.debug(f"CONTEXT: pushing #{len(self.blocks)} {repr(block)}  str {str(block)}")

    def pop(self) -> None:
        """Pop the current block from the context stack.

        Notes:
            Logs a warning when called on an empty stack and does nothing.
        """
        if len(self.blocks) == 0:
            logger.warning("pop() called on empty stack, ignoring")
            return
        logger.debug(f"CONTEXT: popping #{len(self.blocks)} -> #{len(self.blocks) - 1}")
        self.blocks.pop()

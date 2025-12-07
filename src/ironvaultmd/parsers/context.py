import logging
import xml.etree.ElementTree as etree
from dataclasses import dataclass

from ironvaultmd.util import check_dice

logger = logging.getLogger("ironvaultmd")


@dataclass
class RollResult:
    score: int
    vs1: int
    vs2: int
    hitmiss: str
    match: bool


class RollContext:
    def __init__(self):
        self.action = 0
        self.stat = 0
        self.adds = 0
        self.vs1 = 0
        self.vs2 = 0
        self.momentum = 0
        self.progress = 0
        self.rolled = False

    def roll(self, action: int | str, stat: int | str, adds: int | str, vs1: int | str, vs2: int | str) -> RollResult:
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
        if self.rolled:
            logger.warning("RollContext progress-roll with existing roll data")

        self.progress = int(progress)
        self.vs1 = int(vs1)
        self.vs2 = int(vs2)
        self.rolled = True

        return self.get()

    def reroll(self, die: str, value: int | str) -> RollResult:
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
        if not self.rolled:
            logger.warning("RollContext momentum burn without existing roll data")

        if self.progress > 0:
            logger.warning("Attempting to burn momentum for progress roll, ignoring")
        else:
            self.momentum = int(value)

        return self.get()

    def get(self) -> RollResult:
        if self.progress > 0:
            score = self.progress
        elif self.momentum > 0:
            score = self.momentum
        else:
            score = min(self.action + self.stat + self.adds, 10)

        hitmiss, match = check_dice(score, self.vs1, self.vs2)
        return RollResult(score, self.vs1, self.vs2, hitmiss, match)


class BlockContext:
    def __init__(self, name: str, root: etree.Element):
        self.name = name
        self.root = root
        self.roll = RollContext()


class Context:
    def __init__(self, root: etree.Element):
        self.root = root
        self.blocks: list[BlockContext] = []

    @property
    def parent(self) -> etree.Element:
        if len(self.blocks) > 0:
            return self.blocks[-1].root
        return self.root

    @property
    def name(self) -> str:
        if len(self.blocks) == 0:
            return "root"
        return self.blocks[-1].name

    @property
    def roll(self) -> RollContext | None:
        if len(self.blocks) == 0:
            return None
        return self.blocks[-1].roll

    def push(self, name: str, element: etree.Element) -> None:
        block = BlockContext(name, element)
        self.blocks.append(block)
        logger.debug(f"CONTEXT: pushing #{len(self.blocks)} {repr(block)}  str {str(block)}")

    def pop(self) -> None:
        if len(self.blocks) == 0:
            logger.warning("pop() called on empty stack, ignoring")
            return
        logger.debug(f"CONTEXT: popping #{len(self.blocks)} -> #{len(self.blocks) - 1}")
        self.blocks.pop()

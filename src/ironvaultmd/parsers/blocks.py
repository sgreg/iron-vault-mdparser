import logging
import xml.etree.ElementTree as etree
from typing import Any

from ironvaultmd.parsers.base import MechanicsBlockParser
from ironvaultmd.parsers.context import Context
from ironvaultmd.util import create_div

logger = logging.getLogger("ironvaultmd")

class MoveBlockParser(MechanicsBlockParser):
    def __init__(self):
        regex = r'"\[(?P<move_name>[^]]+)]\((?P<move_link>[^)]+)\)"'
        super().__init__("Move", regex)

    def populate(self, data: dict[str, str | Any], ctx: Context) -> etree.Element:
        logger.info(f"help I barely an Idea what I'm doing, data {data}")
        element = create_div(ctx.parent, ["move"])
        create_div(element, ["move-name"]).text = f"{data["move_name"]}"
        return element

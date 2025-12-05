import logging
import xml.etree.ElementTree as etree
from typing import Any

from ironvaultmd.parsers.base import MechanicsBlockParser
from ironvaultmd.parsers.context import Context
from ironvaultmd.util import create_div, convert_link_name

logger = logging.getLogger("ironvaultmd")


# These should probably all use some templates as well


class ActorBlockParser(MechanicsBlockParser):
    def __init__(self):
        regex = r'^name="\[\[.*\|(?P<name>.*)\]\]"$'
        super().__init__("Actor", regex)

    def create_child_element(self, data: dict[str, str | Any], ctx: Context) -> etree.Element:
        element = create_div(ctx.parent, ["actor"])
        create_div(element, ["actor-name"]).text = f"{data["name"]}"
        return element


class MoveBlockParser(MechanicsBlockParser):
    def __init__(self):
        regex = r'"\[(?P<move_name>[^]]+)]\((?P<move_link>[^)]+)\)"'
        super().__init__("Move", regex)

    def create_child_element(self, data: dict[str, str | Any], ctx: Context) -> etree.Element:
        element = create_div(ctx.parent, ["move"])
        create_div(element, ["move-name"]).text = f"{data["move_name"]}"
        return element


class OracleGroupBlockParser(MechanicsBlockParser):
    def __init__(self):
        regex = r'^name="(?P<name>[^"]*)"$'
        super().__init__("Oracle Group", regex)

    def create_child_element(self, data: dict[str, str | Any], ctx: Context) -> etree.Element:
        element = create_div(ctx.parent, ["oracle-block"])
        create_div(element, ["oracle-name"]).text = f"Oracle: {data["name"]}"
        return element


class OracleBlockParser(MechanicsBlockParser):
    def __init__(self):
        regex = r'^name="\[(?P<oracle_name>[^\]]+)\]\(datasworn:.+\)" result="(?P<result>[^"]+)" roll=(?P<roll>\d+)$'
        super().__init__("Oracle", regex)

    def create_child_element(self, data: dict[str, str | Any], ctx: Context) -> etree.Element:
        element = create_div(ctx.parent, ["oracle-block"])
        create_div(element, ["oracle-name"]).text = f"Oracle {convert_link_name(data["oracle_name"])} rolled a {data["roll"]} == {data["result"]}"
        return element


class OraclePromptBlockParser(MechanicsBlockParser):
    def __init__(self):
        regex = r'^"(?P<comment>[^"]*)"$'
        super().__init__("Oracle Prompt", regex)

    def create_child_element(self, data: dict[str, str | Any], ctx: Context) -> etree.Element:
        element = create_div(ctx.parent, ["oracle-block"])
        create_div(element, ["oracle-name"]).text = f"Oracle: {data["comment"]}"
        return element

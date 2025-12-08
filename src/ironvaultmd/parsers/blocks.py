import logging
import xml.etree.ElementTree as etree
from dataclasses import asdict
from typing import Any

from ironvaultmd.parsers.base import MechanicsBlockParser
from ironvaultmd.parsers.context import Context
from ironvaultmd.parsers.templater import templater
from ironvaultmd.util import create_div, convert_link_name

logger = logging.getLogger("ironvaultmd")


# These should probably all use some templates as well


class ActorBlockParser(MechanicsBlockParser):
    def __init__(self):
        regex = r'^name="\[\[.*\|(?P<name>.*)\]\]"$'
        super().__init__("Actor", regex)

    def create_root(self, data: dict[str, str | Any], ctx: Context) -> etree.Element:
        element = create_div(ctx.parent, ["actor"])
        create_div(element, ["actor-name"]).text = f"{data["name"]}"
        return element


class MoveBlockParser(MechanicsBlockParser):
    def __init__(self):
        regex = r'"\[(?P<move_name>[^]]+)]\((?P<move_link>[^)]+)\)"'
        super().__init__("Move", regex)

    def create_root(self, data: dict[str, str | Any], ctx: Context) -> etree.Element:
        element = create_div(ctx.parent, ["move"])
        create_div(element, ["move-name"]).text = f"{data["move_name"]}"
        return element

    def finalize(self, ctx):
        if not ctx.roll.rolled:
            logger.debug("No roll context, skipping")
            return

        result = ctx.roll.get()

        # Add the final roll result as an own <div>
        template = templater.get_template("roll_result")
        if template is not None:
            element = etree.fromstring(template.render(asdict(result)))
            ctx.parent.append(element)

        # Style the main move block <div> with classes based on the roll result
        class_hitmiss = f"ivm-move-result-{result.hitmiss}"
        class_match = "ivm-move-result-match" if result.match else ""
        current_classes = ctx.parent.get("class", "")

        new_classes = " ".join(c for c in [current_classes, class_hitmiss, class_match] if c)
        ctx.parent.set("class", new_classes)


class OracleGroupBlockParser(MechanicsBlockParser):
    def __init__(self):
        regex = r'^name="(?P<name>[^"]*)"$'
        super().__init__("Oracle Group", regex)

    def create_root(self, data: dict[str, str | Any], ctx: Context) -> etree.Element:
        element = create_div(ctx.parent, ["oracle-block"])
        create_div(element, ["oracle-name"]).text = f"Oracle: {data["name"]}"
        return element


class OracleBlockParser(MechanicsBlockParser):
    def __init__(self):
        # See the oracle node parser, there can be two types (that I know of so far):
        # oracle name="[Core Oracles \/ Theme](datasworn:oracle_rollable:starforged\/core\/theme)" result="Warning" roll=96
        # oracle name="Will [[Lone Howls\/Clocks\/Clock decrypt Verholm research.md|Clock decrypt Verholm research]] advance? (Likely)" result="No" roll=83
        regex = r'^name="(\[(?P<oracle_name>[^\]]+)\]\(datasworn:.+\)|(?P<oracle_text>[^"]+))" result="(?P<result>[^"]+)" roll=(?P<roll>\d+)$'
        super().__init__("Oracle", regex)

    def create_root(self, data: dict[str, str | Any], ctx: Context) -> etree.Element:
        # This is also taken straight from the oracle node parser.
        # Should probably combine those to some common place?
        oracle = "undefined"
        if data["oracle_name"] is not None:
            oracle = convert_link_name(data["oracle_name"])
        elif data["oracle_text"] is not None:
            oracle = convert_link_name(data["oracle_text"])

        element = create_div(ctx.parent, ["oracle-block"])
        create_div(element, ["oracle-name"]).text = f"Oracle {oracle} rolled a {data["roll"]} == {data["result"]}"
        return element


class OraclePromptBlockParser(MechanicsBlockParser):
    def __init__(self):
        regex = r'^"(?P<comment>[^"]*)"$'
        super().__init__("Oracle Prompt", regex)

    def create_root(self, data: dict[str, str | Any], ctx: Context) -> etree.Element:
        element = create_div(ctx.parent, ["oracle-block"])
        create_div(element, ["oracle-name"]).text = f"Oracle: {data["comment"]}"
        return element

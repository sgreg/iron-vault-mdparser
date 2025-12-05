import logging
import re
import xml.etree.ElementTree as etree
from dataclasses import asdict
from typing import Any

from jinja2 import Template

from ironvaultmd.parsers.context import Context
from ironvaultmd.parsers.templater import templater
from ironvaultmd.util import create_div

logger = logging.getLogger("ironvaultmd")



class NodeParser:
    """Parser for iron-vault-mechanics nodes supporting regex matching"""
    node_name: str
    regex: re.Pattern[str]
    template: Template

    def __init__(self, name: str, regex: str) -> None:
        self.node_name = name
        self.regex = re.compile(regex)
        self.template = templater.get_template(name)

    def _match(self, data: str) -> dict[str, str | Any] | None:
        """Try to match the given data string to the parser's regex object and return match group dictionary"""
        match = self.regex.search(data)

        if match is None:
            logger.warning(f"Fail to match parameters for {self.node_name}: {repr(data)}")
            return None

        logger.debug(match)
        return match.groupdict()

    def parse(self, ctx: Context, data: str) -> None:
        matches = self._match(data)
        if matches is None:
            return

        args = self.create_args(matches, ctx)
        out = self.template.render(args)
        # store `out` in context somewhere, and have within context (or somewhere) append to parents on pop() or so
        ctx.parent.append(etree.fromstring(out))

    def create_args(self, data: dict[str, str | Any], _: Context) -> dict[str, str | Any]:
        return data


class FallbackNodeParser(NodeParser):
    def __init__(self, name: str):
        regex = "(?P<content>.*)"
        self.name = name
        super().__init__("Node", regex)

    def create_args(self, data: dict[str, str | Any], _: Context) -> dict[str, str | Any]:
        return {"node_name": self.name, "content": data["content"]}


class MechanicsBlockParser: # there's already a BlockParser in Markdown itself, so let's just best use another name
    def __init__(self, name:str, regex: str):
        self.block_name = name
        self.regex = re.compile(regex)

    def _match(self, data: str) -> dict[str, str | Any] | None:
        """Try to match the given data string to the parser's regex object and return match group dictionary"""
        match = self.regex.search(data)

        if match is None:
            logger.warning(f"Fail to match parameters for block {self.block_name}: {repr(data)}")
            return None

        logger.debug(match)
        return match.groupdict()

    def parse(self, ctx: Context, data: str) -> etree.Element:
        matches = self._match(data)
        if matches is None:
            raise Exception("shoulda match")

        return self.populate(matches, ctx)

    def populate(self, _: dict[str, str | Any], __: Context) -> etree.Element:
        raise NotImplementedError


class FallbackBlockParser(MechanicsBlockParser):
    def __init__(self, name: str):
        regex = "(?P<content>.*)"
        self.name = name
        super().__init__("Block", regex)

    def populate(self, data: dict[str, str | Any], ctx: Context) -> etree.Element:
        logger.info(f"help I have no Idea what I'm doing, data {data}")
        element = create_div(ctx.parent, ["block-" + self.name])
        element.text = f"{self.name}: {data["content"]}"
        return element


# TODO: find a better home for this
def add_roll_result(ctx: Context):
    if not ctx.roll.rolled:
        logger.debug("No roll context, skipping")
        return

    template = templater.get_template("roll_result")
    element = etree.fromstring(template.render(asdict(ctx.roll.get())))
    ctx.parent.append(element)

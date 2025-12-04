import logging
import re
import xml.etree.ElementTree as etree
from dataclasses import asdict
from typing import Any

from jinja2 import Template

from ironvaultmd.parsers.context import Context
from ironvaultmd.parsers.templater import templater

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


# TODO: find a better home for this
def add_roll_result(ctx: Context):
    if not ctx.roll.rolled:
        logger.debug("No roll context, skipping")
        return

    template = templater.get_template("roll_result")
    element = etree.fromstring(template.render(asdict(ctx.roll.get())))
    ctx.parent.append(element)

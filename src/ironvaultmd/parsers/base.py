import logging
import re
import xml.etree.ElementTree as etree
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

    def begin(self, ctx: Context, data: str) -> etree.Element:
        matches = self._match(data)
        if matches is None:
            element = create_div(ctx.parent, ["block"])
            element.text = f"{self.block_name}: {data}"
            return element

        return self.create_root(matches, ctx)

    def create_root(self, data: dict[str, str | Any], ctx: Context) -> etree.Element:
        raise NotImplementedError

    def finalize(self, ctx):
        # To be overridden by child classes as needed, do nothing by default
        pass

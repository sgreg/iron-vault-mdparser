import logging
import re
import traceback
import xml.etree.ElementTree as etree
from typing import Any

from jinja2 import TemplateNotFound, PackageLoader, Environment, Template


logger = logging.getLogger("ironvaultmd")


class Templater:
    def __init__(self):
        self.template_loader = PackageLoader('ironvaultmd.parsers', 'templates')
        self.template_env = Environment(loader=self.template_loader, autoescape=True)

    def get(self, name: str, strict: bool = False) -> Template | None:
        if not name.endswith(".html"):
            filename = f"{name.lower().replace(' ', '-')}.html"
        else:
            filename = name

        try:
            return self.template_env.get_template(filename)
        except TemplateNotFound as err:
            logger.warning(f"Template {filename} not found")
            logger.debug(''.join(traceback.TracebackException.from_exception(err).format()))
            if strict:
                raise err
            return None

templater = Templater()


class NodeParser:
    """Parser for iron-vault-mechanics nodes supporting regex matching"""
    node_name: str
    regex: re.Pattern[str]
    template: Template

    def __init__(self, name: str, regex: str) -> None:
        self.node_name = name
        self.regex = re.compile(regex)
        self.template = templater.get(name, strict=True)

    def _match(self, data: str) -> dict[str, str | Any] | None:
        """Try to match the given data string to the parser's regex object and return match group dictionary"""
        match = self.regex.search(data)

        if match is None:
            logger.warning(f"Fail to match parameters for {self.node_name}: {repr(data)}")
            return None

        logger.debug(match)
        return match.groupdict()

    def parse(self, parent: etree.Element, data: str) -> None:
        matches = self._match(data)
        if matches is None:
            return

        args = self.create_args(matches)
        out = self.template.render(args)
        parent.append(etree.fromstring(out))

    def create_args(self, data: dict[str, str | Any]) -> dict[str, str | Any]:
        return data


class FallbackNodeParser(NodeParser):
    def __init__(self, name: str):
        regex = "(?P<content>.*)"
        self.name = name
        super().__init__("Node", regex)

    def create_args(self, data: dict[str, str | Any]) -> dict[str, str | Any]:
        return {"node_name": self.name, "content": data["content"]}

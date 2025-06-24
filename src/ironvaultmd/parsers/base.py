import logging
import re
import xml.etree.ElementTree as etree
from typing import Any

from jinja2 import Template

from ironvaultmd.templater import templater

logger = logging.getLogger("ironvaultmd")


class TemplateRegexNodeParser:
    """Parser for iron-vault-mechanics nodes supporting regex matching"""
    node_name: str
    regex: re.Pattern[str]
    template: Template

    def __init__(self, name: str, regex: str, template: str | None) -> None:
        self.node_name = name
        self.regex = re.compile(regex)
        if template is None:
            self.template = templater.get(name, strict=True)
        else:
            self.template = Template(template)

    def __match(self, data: str) -> dict[str, str | Any] | None:
        """Try to match the given data string to the parser's regex object and return match group dictionary"""
        match = self.regex.search(data)

        if match is None:
            logger.warning(f"Fail to match parameters for {self.node_name}: {repr(data)}")
            return None

        logger.debug(match)
        return match.groupdict()

    def parse(self, parent: etree.Element, data: str) -> None:
        matches = self.__match(data)
        if matches is None:
            return

        # template = templater.get(self.node_name)
        # if template is None:
        #     return

        args = self.create_args(matches)
        out = self.template.render(args)
        parent.append(etree.fromstring(out))

    def create_args(self, data: dict[str, str | Any]) -> dict[str, str | Any]:
        return data


class FallbackNodeParser(TemplateRegexNodeParser):
    def __init__(self, name: str):
        regex = "(?P<content>.*)"
        template = '<div class="ivm-node">{{ node_name }}: {{ content }}</div>'
        super().__init__(name, regex, template)

    def create_args(self, data: dict[str, str | Any]) -> dict[str, str | Any]:
        return {"node_name": self.node_name, "content": data["content"]}

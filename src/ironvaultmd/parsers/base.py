import logging
import re
import xml.etree.ElementTree as etree
from dataclasses import dataclass
from typing import Any

from jinja2 import Template, PackageLoader, Environment, TemplateNotFound

logger = logging.getLogger("ironvaultmd")

@dataclass
class UserTemplates:
    # Nodes
    add: str | None = None
    burn: str | None = None
    clock: str | None = None
    meter: str | None = None
    ooc: str | None = None
    oracle: str | None = None
    position: str | None = None
    progress: str | None = None
    progress_roll: str | None = None
    reroll: str | None = None
    roll: str | None = None
    track: str | None = None
    # Other elements
    link: str | None = None


class Templater:
    def __init__(self):
        self.template_loader = PackageLoader('ironvaultmd.parsers', 'templates')
        self.template_env = Environment(loader=self.template_loader, autoescape=True)
        self.user_templates = UserTemplates()

    def load_user_templates(self, user_templates: UserTemplates):
        for name, value in user_templates.__dict__.items():
            if value is not None:
                logger.debug(f"Setting user template for '{name}': '{value}'")
                self.user_templates.__dict__[name] = value
            else:
                # In case there are multiple calls to this method, ensure that
                # potentially previously set user templates are reset to None
                self.user_templates.__dict__[name] = None


    def get_template(self, name: str) -> Template:
        logger.debug(f"Getting template for '{name}'")
        key = name.lower().replace(' ', '_')

        user_template = self.user_templates.__dict__.get(key, None)
        if isinstance(user_template, str):
            logger.debug("  -> found user template")
            return Template(user_template)

        filename = f"{key}.html"

        try:
            logger.debug("  -> using default template")
            return self.template_env.get_template(filename)
        except TemplateNotFound as err:
            logger.warning(f"Template {filename} not found")
            raise err

templater = Templater()


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

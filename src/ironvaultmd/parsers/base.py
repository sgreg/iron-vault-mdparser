import logging
import re
import xml.etree.ElementTree as etree
from typing import Any

from jinja2 import Template

from ironvaultmd.templater import templater
from ironvaultmd.util import create_div

logger = logging.getLogger("ironvaultmd")


# Next step for this: add Jinja2 templates!
# Something like this should work:
"""
from jinja2 import Template
import xml.etree.ElementTree as etree

t = Template('<div class="{{ classes }}">Hello, {{ name }}!</div>')
out = t.render(classes='ivm-bob bold', name='Blob Bob')
tree = etree.fromstring(out)

-> creates an etree Element that can then be attached to the parent element
-> each subclass has then a default template defined here, which can (as next step) be adjusted by user

"""

class NodeParser:
    """Most elemental base parser for iron-vault-mechanics nodes"""

    def __init__(self, name: str) -> None:
        self.node_name = name

    def parse(self, parent: etree.Element, data: str) -> None:
        """Parse the given data, create HTML elements from it, and attach it to the given parent element"""
        # element = create_div(parent, ["node"])
        # element.text = f"<i>{self.node_name}</i>: {data}"

        # Note, there's some issue with this here, causing test_base_parsers.py test_parser_node() fail.
        # Setting element.text directly seems to escape the HTML tags automatically, so searching in the
        # text itself succeeds. Without escaping the <i></i> tags here, the text content is actually None,
        # presumably because it has a child Element right away there.
        # Manually escaping it makes the test work again, but not sure if I like the idea of this.
        t = Template('<div class="{{ classes }}">&lt;i&gt;{{ node_name }}&lt;/i&gt;: {{ data }}</div>')
        out = t.render(classes="ivm-node", node_name=self.node_name, data=data)
        logger.info(out)
        e = etree.fromstring(out)
        parent.append(e)


class RegexNodeParser(NodeParser):
    """Parser for iron-vault-mechanics nodes supporting regex matching"""
    regex: re.Pattern[str]

    def __init__(self, name: str, regex: str) -> None:
        super().__init__(name)
        self.regex = re.compile(regex)

    def __match(self, data: str) -> dict[str, str | Any] | None:
        """Try to match the given data string to the parser's regex object and return match group dictionary"""
        match = self.regex.search(data)

        if match is None:
            logger.warning(f"Fail to match parameters for {self.node_name}: {repr(data)}")
            return None

        logger.debug(match)
        return match.groupdict()

    def parse(self, parent: etree.Element, data: str) -> None:
        p = self.__match(data)
        if p is None:
            return

        self.set_element(parent, p)

    def set_element(self, parent: etree.Element, data: dict[str, str | Any]) -> None:
        """Parser subclass specific method to set element data to the given parent element"""
        raise NotImplementedError


class TemplateRegexNodeParser(NodeParser):
    """Parser for iron-vault-mechanics nodes supporting regex matching"""
    regex: re.Pattern[str]

    def __init__(self, name: str, regex: str, template: str | None) -> None:
        super().__init__(name)
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


class SimpleContentNodeParser(RegexNodeParser):
    """Parser for iron-vault-mechanics nodes to simply set node content text"""
    def __init__(self, name: str, regex: str, divs: list[str]) -> None:
        self.divs = divs
        super().__init__(name, regex)

    def set_element(self, parent: etree.Element, data: dict[str, str | Any]) -> None:
        """Create `<div>` element object with the CSS classes passed to the constructor and call set_content"""
        element = create_div(parent, self.divs)
        self.set_content(element, data)

    def set_content(self, element: etree.Element, data: dict[str, str | Any]) -> None:
        """Parser subclass specific method to set up the given element's content"""
        raise NotImplementedError
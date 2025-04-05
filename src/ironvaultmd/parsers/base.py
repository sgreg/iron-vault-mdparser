import re
import xml.etree.ElementTree as etree
from typing import Any

from ironvaultmd.util import create_div


class NodeParser:
    """Most elemental base parser for iron-vault-mechanics nodes"""

    def __init__(self, name: str) -> None:
        self.node_name = name


    def parse(self, parent: etree.Element, data: str) -> None:
        """Parse the given data, create HTML elements from it, and attach it to the given parent element"""
        parent.text = f"<i>{self.node_name}</i>: {data}"


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
            print(f"Fail to match parameters for {self.node_name}: {repr(data)}")
            return None

        print(match)
        return match.groupdict()

    def parse(self, parent: etree.Element, data: str) -> None:
        p = self.__match(data)
        if p is None:
            return

        self.set_element(parent, p)

    def set_element(self, parent: etree.Element, data: dict[str, str | Any]) -> None:
        """Parser subclass specific method to set element data to the given parent element"""
        raise NotImplementedError


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
import logging
import xml.etree.ElementTree as etree

logger = logging.getLogger("ironvaultmd")


class Context:
    def __init__(self, parent: etree.Element):
        self._elements: list[etree.Element] = [parent]

    @property
    def parent(self) -> etree.Element:
        return self._elements[-1]

    def push(self, element: etree.Element) -> None:
        self._elements.append(element)

    def pop(self) -> None:
        if len(self._elements) == 1:
            logger.warning("Attempting to remove last context element, ignoring")
            return
        self._elements.pop()

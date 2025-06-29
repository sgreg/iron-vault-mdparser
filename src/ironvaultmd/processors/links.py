import re
import xml.etree.ElementTree as etree
from dataclasses import dataclass

from markdown.inlinepatterns import InlineProcessor

from ironvaultmd.parsers.base import templater


@dataclass
class Link:
    ref: str
    label: str

class WikiLinkProcessor(InlineProcessor):
    """Markdown inline processor for handling wikilinks.

    This is intended to replace Python Markdown's own wikilinks extension, for few reasons:
     1. The original wikilinks extension doesn't handled piped links, i.e. links in the
     style of [[link|label]] -> <a href="link">label</a> and there appears to be no
     motivation to change that (and earlier attempts have been shut down).
     Obsidian and the iron-vault plugin make good use of that though, so there is good
     reason to have it added.
     2. Currently, linking itself is still a bit of an unknown subject regarding how I'd
     want that to happen in practice. So for now, it just extracts the link/label and
     returns a <span class="ivm-link">label</span> instead of an actual link.
     This is expected to change eventually.
     3. Expanding on the previous reason, links themselves are collected in a dedicated
     list while being parsed. This allows some additional handling of links in the code
     using this extension. Maybe. Well, I got some ideas and plans with that at least.
    """

    def __init__(self, links: list[Link] | None = None):
        if links is not None and not isinstance(links, list):
            raise TypeError("Parameter 'links' must be a list")

        # [[link as label]]
        # [[link|label]]
        wikilink_pattern = r'\[\[([^]|]+)(?:\|([^]]+))?]]'
        self.links = links
        self.template = templater.get_template("link")
        super().__init__(wikilink_pattern)

    def handleMatch(self, m: re.Match[str], data: str) -> tuple[etree.Element | str, int, int]:
        if m.group(1).strip():
            ref = m.group(1).strip()
            label = m.group(2)

            if label is not None:
                # Piped wikilink with a dedicated label text.
                label = label.strip()
            if not label:
                # Not a piped link, or label text was empty,
                # use the link as label text instead then.
                label = ref

            link = Link(ref, label)
            element = etree.fromstring(self.template.render(link.__dict__))

            if self.links is not None:
                self.links.append(link)

        else:
            element = ''

        return element, m.start(0), m.end(0)

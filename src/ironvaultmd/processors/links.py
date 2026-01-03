"""Wiki link inline processor for Iron Vault Markdown.

This module provides a Python-Markdown inline processor that parses
Obsidian-style wiki links such as `[[target#anchor|label]]` and renders them
using a Jinja template. Parsed links can optionally be collected for later
processing by the caller.

Example:
    ```python
    from markdown import Markdown
    from ironvaultmd.processors.links import WikiLinkProcessor, LinkCollector

    links = []
    collector = LinkCollector(links)
    md = Markdown()
    md.inlinePatterns.register(WikiLinkProcessor(collector), 'iv-wikilink', 175)
    html = md.convert('See [[page#sect|this section]].')
    assert links[0].ref == 'page'
    assert links[0].label == 'this section'
    ```
"""

import re
import xml.etree.ElementTree as etree
from dataclasses import dataclass

from markdown.inlinepatterns import InlineProcessor

from ironvaultmd.parsers.templater import get_templater


@dataclass
class Link:
    ref: str
    anchor: str
    label: str


class LinkCollector:
    """Link collection class.

    Keeps count of the number of links collected and optionally collects
    the parsed links as `Link` instances in a list.

    The counter is reset to zero when the whole `IronVaultExtension` instance
    is reset. It's also passed to the template during rendering and can be
    used there as a unique (per parsed document) identifier.
    """

    def __init__(self, links: list[Link] | None = None) -> None:
        """Create the collector instance.

        Args:
            links: Optional list where the links are collected into.
        """
        self.links = links
        self.count = 0

    def add(self, link: Link) -> int:
        """Add the given `link` to the collector.

        Increments the link counter and adds the given `Link` instance
        to the internal list - if there is one.

        Args:
            link: Parsed `Link` instance to add.

        Returns:
            Number of collected links.
        """
        if self.links is not None:
            self.links.append(link)
        self.count += 1

        return self.count

    def reset(self) -> None:
        """Reset the collector instance.

        Clears the internal list - if there is one - and sets
        the sequence counter back to zero.
        """
        if self.links:
            self.links.clear()
        self.count = 0


class WikiLinkProcessor(InlineProcessor):
    """Markdown inline processor for handling wiki links.

    This is intended to replace Python Markdown's own wikilinks extension, for few reasons:

     1. The original wikilinks extension doesn't handle piped links, i.e. links in the
        style of `[[link|label]]` -> `<a href="link">label</a>` and there appears to be no
        motivation to change that (and earlier attempts have been shut down).
        Obsidian and the iron-vault plugin make good use of that, though, so there is good
        reason to have it added.
     2. Currently, linking itself is still a bit of an unknown subject regarding how I'd
        want that to happen in practice. So for now, it just extracts the link/label and
        returns a <span class="ivm-link">label</span> instead of an actual link.
        This is expected to change eventually.
     3. Expanding on the previous reason, links themselves are collected in a dedicated
        list while being parsed. This allows some additional handling of links in the code
        using this extension. Maybe. Well, I got some ideas and plans with that at least.

    Attributes:
        links: `LinkCollector` instance holding the link sequence counter,
            and optionally collects parsed `Link` instances.

    Note:
        The actual href resolution is deferred. The processor renders a
        placeholder element using the `link` template, which can be replaced or
        post-processed later.
    """

    def __init__(self, link_collector: LinkCollector) -> None:
        """Create the inline processor.

        Args:
            links: Optional list that will be appended with each parsed `Link`.

        Raises:
            TypeError: If `links` is provided but is not a list.
        """

        # [[link as label]]
        # [[link|label]]
        # [[link#anchor]]
        # [[link#anchor|with label]]
        wikilink_pattern = r'!?\[\[([^]|#]+)(?:#([^|\]]+))?(?:\|([^]]+))?]]'
        self.links = link_collector
        super().__init__(wikilink_pattern)

    def handleMatch(self, m: re.Match[str], data: str) -> tuple[etree.Element | str, int, int]:
        """Handle a single wiki link match.

        Args:
            m: The regular expression match object for the wiki link.
            data: The full source text being processed.

        Returns:
            A tuple of `(element, start, end)` where `element` is the created
            HTML element (or an empty string for no output), and `start`/`end`
            are the slice indices within `data` to be replaced.
        """
        if m.group(1).strip():
            ref = m.group(1).strip()
            anchor = m.group(2)
            label = m.group(3)

            if anchor is not None:
                anchor = anchor.strip()
            else:
                anchor = ""

            if label is not None:
                # Piped wikilink with a dedicated label text.
                label = label.strip()
            if not label:
                # Not a piped link, or label text was empty,
                # use the link as label text instead then.
                label = ref

            link = Link(ref, anchor, label)
            count = self.links.add(link)
            template = get_templater().get_template("link")

            if template:
                args = link.__dict__ | {"seq": count}
                element = etree.fromstring(template.render(args))
            else:
                element = label

        else:
            element = ''

        return element, m.start(0), m.end(0)

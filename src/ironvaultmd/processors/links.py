import re
import xml.etree.ElementTree as etree

from markdown.inlinepatterns import InlineProcessor


class WikiLinkProcessor(InlineProcessor):
    """Markdown inline processor for handling wikilinks.

    This is intended to replace Python Markdown's own wikilinks extension, for two reasons:
     1. The original wikilinks extension doesn't handled piped links, i.e. links in the
     style of [[link|label]] -> <a href="link">label</a> and there appears to be no
     motivation to change that (and earlier attempts have been shut down).
     Obsidian and the iron-vault plugin make good use of that though, so there is good
     reason to have it added.
     2. Currently, linking itself is still a bit of an unknown subject regarding how I'd
     want that to happen in practice. So for now, it just extracts the link/label and
     returns a <span class="ivm-link">label</span> instead of an actual link.
     This is expected to change eventually.
    """

    def __init__(self):
        # [[link as label]]
        # [[link|label]]
        wikilink_pattern = r'\[\[([^]|]+)(?:\|([^]]+))?]]'
        super().__init__(wikilink_pattern)

    def handleMatch(self, m: re.Match[str], data: str) -> tuple[etree.Element | str, int, int]:
        if m.group(1).strip():
            link = m.group(1).strip()
            label = m.group(2)

            if label is not None:
                # Piped wikilink with a dedicated label text.
                label = label.strip()
            if not label:
                # Not a piped link, or label text was empty,
                # use the link as label text instead then.
                label = link

            element = etree.Element('span')
            element.set('class', 'ivm-link')
            element.text = label

        else:
            element = ''

        return element, m.start(0), m.end(0)

import xml.etree.ElementTree as etree

import pytest

from ironvaultmd.parsers.templater import TemplateOverrides, Templater, set_templater
from ironvaultmd.processors.links import Link, LinkCollector
from utils import StringCompareData


def test_linkproc_match_success(linkproc):
    data = [
        StringCompareData("[[link]]", "link"),
        StringCompareData("[[link|label]]", "label"),
        StringCompareData("[[  link  ]]", "link"),
        StringCompareData("[[  link |  label  ]]", "label"),
        StringCompareData("[[multi word link]]", "multi word link"),
        StringCompareData("[[multi word link|multi word label]]", "multi word label"),
        StringCompareData("[[  multi word link  ]]", "multi word link"),
        StringCompareData("[[  multi word link  |  multi word label  ]]", "multi word label"),
        StringCompareData("[[link]] with text afterwards", "link"),
        StringCompareData("[[link|label]] with text afterwards", "label"),
        StringCompareData("this is [[a link without label]] in the middle of it all", "a link without label"),
        StringCompareData("this is [[a link|with a label]] in the middle of it all", "with a label"),
        StringCompareData("first text, and then the [[link]]", "link"),
        StringCompareData("first text, and then the [[link|label]]", "label"),
        StringCompareData("![[embedded link]]", "embedded link"),
        StringCompareData("![[embedded link|label]]", "label"),
        StringCompareData("first text, and then the ![[embedded link]]", "embedded link"),
        StringCompareData("first text, and then the ![[embedded link|label]]", "label"),
        StringCompareData("[[link#anchor]]", "link"),
        StringCompareData("[[link#anchor|label]]", "label"),
    ]

    for d in data:
        match = linkproc.compiled_re.search(d.content)
        element, _, _ = linkproc.handleMatch(match, d.content)

        assert isinstance(element, etree.Element)
        assert element.text == d.expected


def test_linkproc_match_nolink(linkproc):
    data = [
        "[[ ]]",
        "[[ | ]]",
    ]

    for d in data:
        match = linkproc.compiled_re.search(d)
        element, _, _ = linkproc.handleMatch(match, d)

        assert not isinstance(element, etree.Element)
        assert element == ''


def test_linkproc_nomatch(linkproc):
    data = [
        "",
        "[[]]"
        "[[|]]",
        "[[ |]]",
        "[[| ]]",
        # "[[ | ]]" # FIXME this actually matches
        "[[#]]",
        "[[#|]]",
        "[[ #|]]",
        "[[# |]]",
        "[[#| ]]",
        "[[# | ]]",
        #"[[ # | ]]", # FIXME so does hits
        "not a link in sight",
        "[[ open but not closed",
        "[[link|label but not closed",
        "[[link#anchor but not closed",
        "[[link#anchor|label but not closed",
        "same but [[ in the middle of it all",
        "same but [[link|label in the middle of it all",
        "same but [[link#anchor in the middle of it all",
        "same but [[link#anchor|label in the middle of it all",
    ]

    for d in data:
        match = linkproc.compiled_re.search(d)
        assert match is None


def test_linkproc_convert(md):
    data = [
        StringCompareData("[[label]]", "label"),
        StringCompareData("[[link|label]]", "label"),
        StringCompareData("[[multi word link]]", "multi word link"),
        StringCompareData("[[multi word link|multi word label]]", "multi word label"),
        StringCompareData("![[embedded link]]", "embedded link"),
        StringCompareData("![[embedded link|label]]", "label"),
        StringCompareData("![[embedded link|multi word label]]", "multi word label"),
        StringCompareData("[[link#anchor]]", "link"),
        StringCompareData("[[link#anchor|label]]", "label"),
    ]

    template = '<p><span class="ivm-link" id="link-{0}">{1}</span></p>'

    for seq, d in enumerate(data):
        html = md.convert(d.content)
        assert html == template.format(seq + 1, d.expected)


def test_linkproc_collect(linkproc_gen):
    data = [
        "[[link]]",
        "[[different link|label]]",
        "![[embedded link]]",
        "![[embedded link|with label]]",
        "[[link#anchor]]",
        "[[link#anchor|label]]",
        "not a link"
    ]

    links = []
    processor = linkproc_gen(LinkCollector(links))

    for d in data:
        match = processor.compiled_re.search(d)
        if match is not None:
            processor.handleMatch(match, d)

    assert len(links) == 6

    assert isinstance(links[0], Link)
    assert links[0].ref == "link"
    assert links[0].anchor == ""
    assert links[0].label == "link"

    assert isinstance(links[1], Link)
    assert links[1].ref == "different link"
    assert links[0].anchor == ""
    assert links[1].label == "label"

    assert isinstance(links[2], Link)
    assert links[2].ref == "embedded link"
    assert links[0].anchor == ""
    assert links[2].label == "embedded link"

    assert isinstance(links[3], Link)
    assert links[3].ref == "embedded link"
    assert links[0].anchor == ""
    assert links[3].label == "with label"

    assert isinstance(links[4], Link)
    assert links[4].ref == "link"
    assert links[4].anchor == "anchor"
    assert links[4].label == "link"

    assert isinstance(links[5], Link)
    assert links[5].ref == "link"
    assert links[5].anchor == "anchor"
    assert links[5].label == "label"


def test_linkproc_template_override(linkproc_gen, md_gen):
    overrides = TemplateOverrides()
    overrides.link = '<div class="test-class">test link "{{ ref }}" with label "{{ label }}"</div>'

    links = []

    md_gen(links=links, template_overrides=overrides)

    processor = linkproc_gen(LinkCollector(links))

    data = "[[link]]"
    match = processor.compiled_re.search(data)
    assert match is not None
    element, _, _ = processor.handleMatch(match, data)
    assert element.get("class") == "test-class"
    assert element.text == 'test link "link" with label "link"'

    data = "[[different link|label]]"
    match = processor.compiled_re.search(data)
    assert match is not None
    element, _, _ = processor.handleMatch(match, data)
    assert element.get("class") == "test-class"
    assert element.text == 'test link "different link" with label "label"'

    data = "![[embedded link]]"
    match = processor.compiled_re.search(data)
    assert match is not None
    element, _, _ = processor.handleMatch(match, data)
    assert element.get("class") == "test-class"
    assert element.text == 'test link "embedded link" with label "embedded link"'


def test_linkproc_template_override_anchor(linkproc_gen, md_gen):
    overrides = TemplateOverrides()
    overrides.link = '<div class="test-class">test link "{{ ref }}{{ "#" ~ anchor if anchor }}" with label "{{ label }}"</div>'

    links = []

    md_gen(links=links, template_overrides=overrides)

    processor = linkproc_gen(LinkCollector(links))

    data = "[[link]]"
    match = processor.compiled_re.search(data)
    assert match is not None
    element, _, _ = processor.handleMatch(match, data)
    assert element.get("class") == "test-class"
    assert element.text == 'test link "link" with label "link"'

    data = "[[link#anchor]]"
    match = processor.compiled_re.search(data)
    assert match is not None
    element, _, _ = processor.handleMatch(match, data)
    assert element.get("class") == "test-class"
    assert element.text == 'test link "link#anchor" with label "link"'

    data = "[[link#anchor|label]]"
    match = processor.compiled_re.search(data)
    assert match is not None
    element, _, _ = processor.handleMatch(match, data)
    assert element.get("class") == "test-class"
    assert element.text == 'test link "link#anchor" with label "label"'

def test_linkproc_no_template(linkproc_gen, md_gen):
    overrides = TemplateOverrides()
    overrides.link = ''

    links = []

    md_gen(links=links, template_overrides=overrides)

    processor = linkproc_gen(LinkCollector(links))

    data = "[[link]]"
    match = processor.compiled_re.search(data)
    assert match is not None
    element, _, _ = processor.handleMatch(match, data)
    assert isinstance(element, str)
    assert element == "link"

    assert len(links) == 1
    assert links[0].label == "link"

def test_linkproc_template_swap(linkproc_gen, md_gen):
    overrides = TemplateOverrides()
    overrides.link = '<div class="test-class">test link "{{ ref }}" with label "{{ label }}"</div>'

    links = []

    md_gen(links=links, template_overrides=overrides)

    processor = linkproc_gen(LinkCollector(links))

    data = "[[link]]"
    match = processor.compiled_re.search(data)
    assert match is not None
    element, _, _ = processor.handleMatch(match, data)
    assert element.get("class") == "test-class"
    assert element.text == 'test link "link" with label "link"'

    overrides.link = '<div class="another-class">{{ label }}</div>'

    # Verify that tweaking just the value doesn't affect anything yet
    element, _, _ = processor.handleMatch(match, data)
    assert element.get("class") == "test-class"
    assert element.text == 'test link "link" with label "link"'

    templater = Templater(overrides=overrides)
    set_templater(templater)

    element, _, _ = processor.handleMatch(match, data)
    assert element.get("class") == "another-class"
    assert element.text == 'link'


def test_linkcoll():
    links = []
    collector = LinkCollector(links)

    assert collector.links is not None
    assert collector.count == 0

    collector.add("ref1", "anchor1", "label1")
    collector.add("ref2", "anchor2", "label2")

    assert len(links) == 2
    assert len(collector.links) == 2
    assert collector.count == 2

    assert links[0] == collector.links[0]
    assert links[1] == collector.links[1]

    assert links[0].seq == 1
    assert links[1].seq == 2

    collector.reset()

    assert len(links) == 0
    assert len(collector.links) == 0
    assert collector.count == 0

def test_linkcoll_no_links():
    collector = LinkCollector()

    assert collector.links is None
    assert collector.count == 0

    collector.add("ref1", "anchor1", "label1")
    collector.add("ref2", "anchor2", "label2")

    assert collector.links is None
    assert collector.count == 2

    collector.reset()

    assert collector.links is None
    assert collector.count == 0

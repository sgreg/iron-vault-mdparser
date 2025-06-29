import xml.etree.ElementTree as etree

import pytest

from ironvaultmd.parsers.base import UserTemplates, Templater
from ironvaultmd.processors.links import Link
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
        "not a link in sight",
        "[[ open but not closed",
        "[[link|label but not closed",
        "same but [[ in the middle of it all",
        "same but [[link|label in the middle of it all",
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
    ]

    template = '<p><span class="ivm-link">{0}</span></p>'

    for d in data:
        html = md.convert(d.content)
        assert html == template.format(d.expected)


def test_linkproc_collect(linkproc_gen):
    data = [
        "[[link]]",
        "[[different link|label]]",
        "not a link"
    ]

    links = []
    processor = linkproc_gen(links)

    for d in data:
        match = processor.compiled_re.search(d)
        if match is not None:
            processor.handleMatch(match, d)

    assert len(links) == 2

    assert isinstance(links[0], Link)
    assert links[0].ref == "link"
    assert links[0].label == "link"

    assert isinstance(links[1], Link)
    assert links[1].ref == "different link"
    assert links[1].label == "label"


def test_linkproc_collect_invalid_list(linkproc_gen):
    # Ensures that passing not a list as link storage will cause TypeErrors

    with pytest.raises(TypeError):
        links = "string"
        linkproc_gen(links)

    with pytest.raises(TypeError):
        links = {}
        linkproc_gen(links)

    with pytest.raises(TypeError):
        links = ()
        linkproc_gen(links)


def test_linkproc_user_template(linkproc_gen, md_gen):
    user_templates = UserTemplates()
    user_templates.link = '<div class="test-class">test link "{{ ref }}" with label "{{ label }}"</div>'

    links = []

    md_gen(links=links, templates=user_templates)

    processor = linkproc_gen(links)

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

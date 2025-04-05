import xml.etree.ElementTree as etree
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

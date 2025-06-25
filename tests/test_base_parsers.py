import pytest
from jinja2 import Template, TemplateNotFound

from ironvaultmd.parsers.base import FallbackNodeParser, Templater, NodeParser


def test_templater_success():
    templater = Templater()

    valid_names = [
        "roll",
        "Roll",
        "ROLL",
        "roll.html",
        "progress-roll",
        "progress roll",
    ]

    for name in valid_names:
        template = templater.get(name)
        assert template is not None
        assert isinstance(template, Template)

def test_templater_error():
    templater = Templater()

    valid_names = [
        "",
        "non existing",
        "non-existing.html",
    ]

    for name in valid_names:
        assert templater.get(name, strict=False) is None

    for name in valid_names:
        with pytest.raises(TemplateNotFound):
            templater.get(name, strict=True)


def test_parser_fallback(parent):
    node_name = "Node Test"
    parser = FallbackNodeParser(node_name)

    assert parser.node_name == node_name

    content = "Random Content"
    parser.parse(parent, content)

    node = parent.find("div")
    assert node is not None
    assert "ivm-node" in node.get("class")
    assert node_name in node.text
    assert content in node.text


def test_parser_get_template():
    parser = NodeParser("Roll", "", None)
    assert parser.template is not None
    assert isinstance(parser.template, Template)
    assert parser.template.filename.endswith("/roll.html")

    parser = NodeParser("Test", "", "<div>{{ test }}</div>")
    assert parser.template is not None
    assert isinstance(parser.template, Template)
    assert parser.template.filename == "<template>"
    assert parser.template.render(test="test") == "<div>test</div>"

def test_parser_regex_match():
    regex = r'^test data "(?P<test_data>.+)"$'
    parser = NodeParser("Test", regex, "")

    match = parser._match('test data "123"')
    assert match is not None
    assert match.get("test_data", "") == "123"

    no_match = parser._match('nothing that will match')
    assert no_match is None

def test_parser_node_render(parent):
    regex = r'^test data "(?P<test_data>.+)"$'
    template = "<div>data: {{ test_data }}</div>"
    data = 'test data "123"'

    parser = NodeParser("Test", regex, template)

    parser.parse(parent, "no match")
    assert parent.find("div") is None

    parser.parse(parent, data)

    node = parent.find("div")
    assert node is not None
    assert node.text == "data: 123"

def test_parser_args_override(parent):
    regex = r'^test data "(?P<test_data>.+)"$'
    template = "<div>data: {{ test_data }}</div>"
    data = 'test data "123"'

    class TestParser(NodeParser):
        def create_args(self, match):
            return {"test_data": "overridden"}

    parser = TestParser("Test", regex, template)

    parser.parse(parent, "no match")
    assert parent.find("div") is None

    parser.parse(parent, data)

    node = parent.find("div")
    assert node is not None
    assert node.text == "data: overridden"

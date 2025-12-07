import pytest
from jinja2 import Template

from ironvaultmd.parsers.base import FallbackNodeParser, NodeParser, FallbackBlockParser, MechanicsBlockParser


def test_node_fallback(ctx):
    node_name = "Node Test"
    parser = FallbackNodeParser(node_name)

    assert parser.node_name == "Node"
    assert parser.name == node_name

    content = "Random Content"
    parser.parse(ctx, content)

    node = ctx.parent.find("div")
    assert node is not None
    assert "ivm-node" in node.get("class")
    assert node_name in node.text
    assert content in node.text


def test_node_get_template():
    parser = NodeParser("Roll", "")
    assert parser.template is not None
    assert isinstance(parser.template, Template)
    assert parser.template.filename.endswith("/roll.html")

def test_node_regex_match():
    regex = r'^test data "(?P<test_data>.+)"$'
    parser = NodeParser("Node", regex)

    match = parser._match('test data "123"')
    assert match is not None
    assert match.get("test_data", "") == "123"

    no_match = parser._match('nothing that will match')
    assert no_match is None

def test_node_node_render(ctx):
    regex = r'^test data "(?P<test_data>.+)"$'
    data = 'test data "123"'

    parser = NodeParser("Test", regex)

    parser.parse(ctx, "no match")
    assert ctx.parent.find("div") is None

    parser.parse(ctx, data)

    node = ctx.parent.find("div")
    assert node is not None
    assert node.text == "data: 123"

def test_node_args_override(ctx):
    regex = r'^test data "(?P<test_data>.+)"$'
    data = 'test data "123"'

    class TestParser(NodeParser):
        def create_args(self, match, context):
            return {"test_data": "overridden"}

    parser = TestParser("Test", regex)

    parser.parse(ctx, "no match")
    assert ctx.parent.find("div") is None

    parser.parse(ctx, data)

    node = ctx.parent.find("div")
    assert node is not None
    assert node.text == "data: overridden"


def test_block_fallback(ctx):
    name = "test"
    parser = FallbackBlockParser(name)

    assert parser.block_name == name
    assert parser.regex

    content = "Random Content"
    element = parser.begin(ctx, content)
    assert element is not None
    assert "ivm-block" in element.get("class")
    assert "ivm-block-test" in element.get("class")
    assert name in element.text
    assert content in element.text


def test_block_unimplemented(ctx):
    parser = MechanicsBlockParser("name", f'.*')
    with pytest.raises(NotImplementedError):
        parser.begin(ctx, "data")

def test_block_no_match(ctx):
    name = "test"
    data = "value123"
    parser = MechanicsBlockParser(name, f'name="[a-z]*"')
    element = parser.begin(ctx, data)

    # Data won't match, a fallback element is returned, no NotImplementedError should be raised
    assert element is not None
    assert element.get("class") == "ivm-block"
    assert element.text == f"{name}: {data}"

    # Can still call finalize() and nothing will happen
    parser.finalize(ctx)

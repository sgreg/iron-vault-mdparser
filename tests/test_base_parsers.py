import pytest
from jinja2 import Template

from ironvaultmd.parsers.base import NodeParser, MechanicsBlockParser, ParserError
from ironvaultmd.parsers.nodes import RollNodeParser
from ironvaultmd.parsers.templater import templater


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
    parser.parse(ctx, data)

    node = ctx.parent.find("div")
    assert node is not None
    assert node.text == "data: 123"

def test_node_fallback_render(ctx):
    regex = r'^test data "(?P<test_data>.+)"$'
    # This won't match, should fall back to a generic node element
    data = 'no match'

    parser = NodeParser("Test", regex)
    parser.parse(ctx, data)

    node = ctx.parent.find("div")
    assert node is not None
    assert node.text == f"Test: {data}"

def test_node_args_override(ctx):
    regex = r'^test data "(?P<test_data>.+)"$'
    data = 'test data "123"'

    class TestParser(NodeParser):
        def create_args(self, match, context):
            return {"test_data": "overridden"}

    parser = TestParser("Test", regex)
    parser.parse(ctx, data)

    node = ctx.parent.find("div")
    assert node is not None
    assert node.text == "data: overridden"

def test_node_fallback_args_override(ctx):
    regex = r'^test data "(?P<test_data>.+)"$'
    data = 'no match'

    class TestParser(NodeParser):
        def create_args(self, match, context):
            # Verify create_args isn't called when there's no match
            raise Exception("shouldn't have called create_args")

    parser = TestParser("Test", regex)
    parser.parse(ctx, data)

    node = ctx.parent.find("div")
    assert node is not None
    # Verify a generic node element with original data was created, no args override happened
    assert node.text == f"Test: {data}"

def test_node_template_disable(block_ctx):
    # Disable template for this parser
    templater.user_templates.roll = ''

    parser = RollNodeParser()
    assert parser.template is None

    # Verify roll context is reset
    assert not block_ctx.roll.rolled

    # Parse valid data
    data = '"iron" action=3 adds=0 stat=2 vs1=6 vs2=3'
    parser.parse(block_ctx, data)

    # Verify no div element was rendered
    assert block_ctx.parent.find("<div>") is None

    # Verify roll context is set now, even without a template
    assert block_ctx.roll.rolled

    # Verify roll result is as expected from the parsed data
    result = block_ctx.roll.get()
    assert result.score == 5
    assert result.vs1 == 6
    assert result.vs2 == 3
    assert result.hitmiss == "weak"
    assert not result.match

def test_block_no_match(ctx):
    name = "test"
    # Create a parser that only matches small letters
    parser = MechanicsBlockParser(name, r'name="[a-z]*"')
    # Define data that contains not only small letters
    data = "value123"
    element = parser.begin(ctx, data)

    # Data won't match, a fallback "block" element should be returned
    assert element is not None
    assert element.get("class") == "ivm-block"
    assert element.text == f"{name}: {data}"

    # Can still call finalize() and nothing will happen
    parser.finalize(ctx)

def test_block_template_name(ctx):
    name = "oracle"
    data = "value123"
    parser = MechanicsBlockParser(name, r'(?P<test_data>.*)', "test")
    assert parser.template.name == "blocks/test.html"
    element = parser.begin(ctx, data)

    # Verify the "test" template content was created, despite "oracle" would exist
    assert element is not None
    # assert element.get("class") == ""
    assert element.text == f"data: {data}"

    # Can still call finalize() and nothing will happen
    parser.finalize(ctx)

def test_block_no_template(ctx):
    parser = MechanicsBlockParser("test", ".*")

    assert parser.template is not None
    parser.template = None

    # Verify a block parser without template will raise an Exception
    with pytest.raises(ParserError):
        parser.begin(ctx, "test test test")

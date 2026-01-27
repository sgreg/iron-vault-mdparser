from ironvaultmd.parsers.base import (
    NodeParser,
    MechanicsBlockParser,
    ParameterNodeParser,
    ParameterBlockParser,
    ParameterParsingMixin
)
from ironvaultmd.parsers.blocks import MoveBlockParser
from ironvaultmd.parsers.context import NameCollection, Context
from ironvaultmd.parsers.nodes import RollNodeParser, ClockNodeParser
from ironvaultmd.parsers.templater import get_templater, reset_templater
from utils import verify_is_dummy_block_element, element_text


def test_node_regex_match():
    regex = r'^test data "(?P<test_data>.+)"$'
    parser = NodeParser(NameCollection("Node"), regex)

    match = parser._match('test data "123"')
    assert match is not None
    assert match.get("test_data", "") == "123"

    no_match = parser._match('nothing that will match')
    assert no_match is None

def test_param_node_match(ctx):
    parser = ParameterNodeParser(NameCollection("Node"), ["one", "two", "three", "hyphen-param"])
    args = parser._match('one="value one" two=2 three=-3 optional=true hyphen-param="matched" empty="" negative=-5')
    assert args == {
        "one": "value one",
        "two": 2,
        "three": -3,
        "hyphen-param": "matched",
        "extra": {
            "optional": True,
            "empty": "",
            "negative": -5,
        }
    }

    parser = ParameterNodeParser(NameCollection("EmptyKeyNode"), [])
    args = parser._match('one=1 two="a different value"')
    assert args == {
        "extra": {
            "one": 1,
            "two": "a different value"
        }
    }

    parser = ParameterNodeParser(NameCollection("CaseSensitiveParamNode"), ["caseSensitiveKey"])
    args = parser._match('casesensitivekey=false')
    assert args == {
        "extra": {
            "casesensitivekey": False
        }
    }

def test_param_node_no_match(ctx):
    parser = ParameterNodeParser(NameCollection("Node"), ["key"])

    assert parser._match("") is None
    assert parser._match("doesn't have any key value pairs") is None
    assert parser._match("does have some key=value pair but that still won't match") is None
    assert parser._match("key=value pair at the beginning makes no difference here") is None
    assert parser._match("capital-boolean=TRUE") is None
    assert parser._match('key="unbalanced quotes') is None

def test_mixin_parse(ctx):
    # Test the else case in parameter conversion.
    #
    # This shouldn't be possible in reality because the regex won't match.
    # Create new Parser with an extended regex, matching now also "misc" as value,
    # which still isn't covered int he _parse_params() call though.
    class TestParser(ParameterParsingMixin, NodeParser):
        def __init__(self, keys: list[str]) -> None:
            params_regex = r'^(?P<params>(?:[\w-]+=(?:"[^"]*"|\d+|true|false|misc)(?:\s+|$))+)$'
            param_regex = r'([\w-]+)=((?:"[^"]*"|\d+|true|false|misc))'

            super().__init__(NameCollection("Test"), params_regex, param_regex)
            self.known_keys = keys

    # Verify first a valid case (same as in test_param_node_match() above) behaves still the same
    parser = TestParser(["one", "two", "hyphen-param"])
    args = parser._match('one="value one" two=2 optional=true hyphen-param="matched" empty=""')
    assert args == {
        "one": "value one",
        "two": 2,
        "hyphen-param": "matched",
        "extra": {
            "optional": True,
            "empty": "",
        }
    }

    # Sneak in a now-matched, but still not converted value (unchecked=misc)
    match = {"params": 'one="value one" unchecked=misc two=2'}
    args = parser._parse_params(match)

    # Verify the invalid part is simply skipped
    assert args == {
        "one": "value one",
        "two": 2,
        "extra": {}
    }


def test_node_node_render(ctx):
    regex = r'^test data "(?P<test_data>.+)"$'
    data = 'test data "123"'

    parser = NodeParser(NameCollection("Test", "test", "test"), regex)
    parser.parse(ctx, data)

    node = ctx.parent.find("div")
    assert node is not None
    assert node.text == "data: 123"

def test_node_fallback_render(ctx):
    regex = r'^test data "(?P<test_data>.+)"$'
    # This won't match, should fall back to a generic node element
    data = 'no match'

    parser = NodeParser(NameCollection("Test", "test", "test"), regex)
    parser.parse(ctx, data)

    node = ctx.parent.find("div")
    assert node is not None
    assert node.text == f"Test: {data}"

    # Verify later calls don't use the fallback template
    valid_data = 'test data "yes match"'
    parser.parse(ctx, valid_data)
    nodes = ctx.parent.findall("div")

    # Should contain both the old and new div
    assert len(nodes) == 2
    # Verify the first is the initial, not-matched div
    assert nodes[0].text == f"Test: {data}"
    # Verify the second is the matched div and it uses the test template
    assert nodes[1].text == f"data: yes match"


def test_node_args_override(ctx):
    regex = r'^test data "(?P<test_data>.+)"$'
    data = 'test data "123"'

    class TestParser(NodeParser):
        def handle_args(self, match, context):
            return {"test_data": "overridden"}

    parser = TestParser(NameCollection("Test", "test", "test"), regex)
    parser.parse(ctx, data)

    node = ctx.parent.find("div")
    assert node is not None
    assert node.text == "data: overridden"

def test_node_fallback_args_override(ctx):
    regex = r'^test data "(?P<test_data>.+)"$'
    data = 'no match'

    class TestParser(NodeParser):
        def handle_args(self, match, context):
            # Verify create_args isn't called when there's no match
            raise Exception("shouldn't have called create_args")

    parser = TestParser(NameCollection("Test", "test", "test"), regex)
    parser.parse(ctx, data)

    node = ctx.parent.find("div")
    assert node is not None
    # Verify a generic node element with original data was created, no args override happened
    assert node.text == f"Test: {data}"

def test_node_template_disable(block_ctx):
    # Disable template for this parser
    get_templater().overrides.roll = ''

    parser = RollNodeParser()

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
    assert result.stat_name == "iron"
    assert result.score == 5
    assert result.vs1 == 6
    assert result.vs2 == 3
    assert result.hitmiss == "weak"
    assert not result.match

def test_node_template_conditional(ctx):
    parser = ClockNodeParser()

    segment_data = 'from=3 name="Some Clock Progress" out-of=6 to=4'
    status_data = 'name="Some Clock Status" status="added"'

    # First, make sure the segment_data string is actually rendered properly
    parser.parse(ctx, segment_data)
    node = ctx.parent.find("div")
    assert node is not None
    assert "Some Clock Progress" in element_text(node)

    # Reset templater (needed because of internal caching) ...
    reset_templater()
    # ... set up override, rendering only "status" clock strings ...
    get_templater().overrides.clock = """
{% if status %}
<div class="ivm-clock">{{ name }}: {{ status }}</div>
{% endif %}
"""
    # ... and clear previously rendered content.
    ctx.parent.clear()

    # Parse again the same data, verifying nothing is rendered this time
    parser.parse(ctx, segment_data)
    assert ctx.parent.find("div") is None

    # Parse the status_data string to verify that one is still rendered
    parser.parse(ctx, status_data)
    node = ctx.parent.find("div")
    assert node is not None
    assert node.text == "Some Clock Status: added"


def test_block_no_match(ctx):
    names = NameCollection("Test", "test", "actor")
    # Create a parser that only matches small letters
    parser = MechanicsBlockParser(names, r'name="(?P<name>[a-z]*)"')

    # Define data that contains not only small letters
    data = "value123"
    parser.begin(ctx, data)

    # Data won't match, verify it still returns a regular <div> container
    verify_is_dummy_block_element(ctx.parent)

    # Verify fallback args were created
    assert "block_name" in ctx.args.keys()
    assert ctx.args["block_name"] == names.name

    assert "content" in ctx.args.keys()
    assert ctx.args["content"] == data

    # Verify the match group name wasn't added to the args
    assert "name" not in ctx.args.keys()

    # Verify this is rendered to a fallback block template
    parser.finalize(ctx)
    nodes = ctx.root.findall("div")
    assert len(nodes) == 1
    assert nodes[0].get("class") == "ivm-block"
    assert nodes[0].text == "Test: value123"

    # Verify later calls don't use the fallback template
    data = 'name="valid"'
    parser.begin(ctx, data)

    verify_is_dummy_block_element(ctx.parent)

    assert "name" in ctx.args.keys()
    assert ctx.args["name"] == "valid"

    assert "block_name" not in ctx.args.keys()
    assert "content" not in ctx.args.keys()

    # Verify this is rendered now to a valid actor template
    parser.finalize(ctx)
    nodes = ctx.root.findall("div")
    assert len(nodes) == 2

    assert nodes[1].get("class") == "ivm-actor"
    name_node = nodes[1].find("div")
    assert name_node is not None
    assert name_node.text == "valid"

def test_block_node_match(ctx):
    parser = ParameterBlockParser(NameCollection("Block"), ["one", "two", "three", "hyphen-param"])
    args = parser._match('one="value one" two=2 three=-3 optional=true hyphen-param="matched" empty="" negative=-5')
    assert args == {
        "one": "value one",
        "two": 2,
        "three": -3,
        "hyphen-param": "matched",
        "extra": {
            "optional": True,
            "empty": "",
            "negative": -5,
        }
    }

    parser = ParameterBlockParser(NameCollection("EmptyKeyNode"), [])
    args = parser._match('one=1 two="a different value"')
    assert args == {
        "extra": {
            "one": 1,
            "two": "a different value"
        }
    }

    parser = ParameterBlockParser(NameCollection("CaseSensitiveParamNode"), ["caseSensitiveKey"])
    args = parser._match('casesensitivekey=false')
    assert args == {
        "extra": {
            "casesensitivekey": False
        }
    }

def test_block_node_no_match(ctx):
    parser = ParameterBlockParser(NameCollection("Block"), ["key"])

    assert parser._match("") is None
    assert parser._match("doesn't have any key value pairs") is None
    assert parser._match("does have some key=value pair but that still won't match") is None
    assert parser._match("key=value pair at the beginning makes no difference here") is None
    assert parser._match("capital-boolean=TRUE") is None

def test_block_no_template(ctx):
    names = NameCollection("test", "test", "unknown-template")
    parser = MechanicsBlockParser(names, ".*")

    parser.begin(ctx, "test test test")
    verify_is_dummy_block_element(ctx.parent)

    parser.finalize(ctx)

    # Verify there's one parsed div, and it's still just a dummy block
    nodes = ctx.root.findall("div")
    assert len(nodes) == 1
    verify_is_dummy_block_element(nodes[0])

def test_block_template_conditional(parent):
    ctx = Context(parent)
    parser = MoveBlockParser()

    data = '"[Some Move](ignore)" {\n}\n'

    parser.begin(ctx, data)

    parser.finalize(ctx)
    node = ctx.root.find("div")
    assert node is not None
    assert node.get("class") == "ivm-move"

    reset_templater()
    get_templater().overrides.move_block = """
{% if rolled %}
<div class="ivm-move">{{ name }} was rolled</div>
{% endif %}
"""

    ctx.parent.clear()

    parser.begin(ctx, data)
    parser.finalize(ctx)
    node = ctx.root.find("div")
    # Note, this remains a dummy div at this point, no block nodes are removed here
    verify_is_dummy_block_element(node)

    ctx.parent.clear()

    parser.begin(ctx, data)
    ctx.roll.roll("stat", 1, 2, 3, 4, 5)
    parser.finalize(ctx)
    node = ctx.root.find("div")
    assert node is not None
    assert node.text == "Some Move was rolled"

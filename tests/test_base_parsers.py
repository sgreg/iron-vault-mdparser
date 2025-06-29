import pytest
from jinja2 import Template, TemplateNotFound

from ironvaultmd.parsers.base import FallbackNodeParser, NodeParser, Templater, UserTemplates
from ironvaultmd.parsers.nodes import AddNodeParser


def test_templater_success():
    templater = Templater()

    valid_names = [
        "roll",
        "Roll",
        "ROLL",
        "progress_roll",
        "progress roll",
    ]

    for name in valid_names:
        template = templater.get_template(name)
        assert template is not None
        assert isinstance(template, Template)

def test_templater_error():
    templater = Templater()

    invalid_names = [
        "",
        "non existing",
        "non-existing.html",
        "progress-roll",
        "roll.html",
    ]

    for name in invalid_names:
        with pytest.raises(TemplateNotFound):
            templater.get_template(name)


def test_parser_fallback(parent):
    node_name = "Node Test"
    parser = FallbackNodeParser(node_name)

    assert parser.node_name == "Node"
    assert parser.name == node_name

    content = "Random Content"
    parser.parse(parent, content)

    node = parent.find("div")
    assert node is not None
    assert "ivm-node" in node.get("class")
    assert node_name in node.text
    assert content in node.text


def test_parser_get_template():
    parser = NodeParser("Roll", "")
    assert parser.template is not None
    assert isinstance(parser.template, Template)
    assert parser.template.filename.endswith("/roll.html")

def test_parser_regex_match():
    regex = r'^test data "(?P<test_data>.+)"$'
    parser = NodeParser("Node", regex)

    match = parser._match('test data "123"')
    assert match is not None
    assert match.get("test_data", "") == "123"

    no_match = parser._match('nothing that will match')
    assert no_match is None

def test_parser_node_render(parent):
    regex = r'^test data "(?P<test_data>.+)"$'
    data = 'test data "123"'

    parser = NodeParser("Test", regex)

    parser.parse(parent, "no match")
    assert parent.find("div") is None

    parser.parse(parent, data)

    node = parent.find("div")
    assert node is not None
    assert node.text == "data: 123"

def test_parser_args_override(parent):
    regex = r'^test data "(?P<test_data>.+)"$'
    data = 'test data "123"'

    class TestParser(NodeParser):
        def create_args(self, match):
            return {"test_data": "overridden"}

    parser = TestParser("Test", regex)

    parser.parse(parent, "no match")
    assert parent.find("div") is None

    parser.parse(parent, data)

    node = parent.find("div")
    assert node is not None
    assert node.text == "data: overridden"


def test_user_template_load():
    templater = Templater()

    user_templates = UserTemplates()
    user_templates.add = '<div class="test-class">test add</div>'
    user_templates.meter = '<div class="test-class">test meter</div>'

    templater.load_user_templates(user_templates)

    add_template = templater.get_template("add")
    meter_template = templater.get_template("meter")
    roll_template = templater.get_template("roll")

    assert add_template.filename == "<template>"
    assert meter_template.filename == "<template>"
    assert roll_template.filename.endswith("/roll.html")


def test_user_template_render(md_gen, parent):
    user_templates = UserTemplates()
    user_templates.add = '<div class="test-class">test add with value {{ add }}</div>'

    md_gen(templates=user_templates)

    add_parser = AddNodeParser()
    assert add_parser.template.filename == "<template>"

    add_parser.parse(parent, '2 "for test reasons"')
    node = parent.find("div")

    assert node is not None
    assert node.get("class") == "test-class"
    assert node.text == "test add with value 2"

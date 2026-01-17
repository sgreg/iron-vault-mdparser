import pytest
from jinja2 import Template, PackageLoader

from ironvaultmd.parsers.blocks import ActorBlockParser
from ironvaultmd.parsers.nodes import AddNodeParser, MeterNodeParser
from ironvaultmd.parsers.templater import Templater, TemplateOverrides, get_templater, set_templater, clear_templater
from utils import verify_is_dummy_block_element


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
        template = templater.get_template(name, "nodes")
        assert template is not None
        assert isinstance(template, Template)

def test_templater_not_found():
    templater = Templater()

    invalid_names = [
        "",
        "non existing",
        "non-existing.html",
        "progress-roll",
        "roll.html",
    ]

    for name in invalid_names:
        assert templater.get_template(name, "nodes") is None

def test_templater_invalid_type():
    templater = Templater()

    # Verify invalid template type value will return None
    template = templater.get_template("move", "invalid")
    assert template is None

def test_templater_unknown_names():
    templater = Templater()

    types = ["blocks", "nodes", ""]
    for template_type in types:
        assert templater.get_template("unknown", template_type) is None

def test_user_overrides_load():
    templater = Templater()

    overrides = TemplateOverrides()
    overrides.add = '<div class="test-class">test add</div>'
    overrides.meter = '<div class="test-class">test meter</div>'
    overrides.actor_block = '<div class="test-class"></div>'

    templater.load_user_overrides(overrides)

    add_template = templater.get_template("add", "nodes")
    meter_template = templater.get_template("meter", "nodes")
    roll_template = templater.get_template("roll", "nodes")
    actor_template = templater.get_template("actor", "blocks")

    assert add_template.filename == "<template>"
    assert meter_template.filename == "<template>"
    assert roll_template.filename.endswith("/roll.html")
    assert actor_template.filename == "<template>"

def test_user_overrides_load_invalid():
    templater = Templater()

    templater.load_user_overrides(None)

    add_template = templater.get_template("add", "nodes")
    meter_template = templater.get_template("meter", "nodes")

    assert add_template.filename.endswith("/add.html")
    assert meter_template.filename.endswith("/meter.html")

def test_user_overrides_render_node(md_gen, ctx):
    overrides = TemplateOverrides()
    overrides.add = '<div class="test-class">test add with value {{ add }}</div>'
    overrides.actor_block = '<div class="test-class"><div class="actor">Actor {{ name }}</div></div>'

    md_gen(template_overrides=overrides)

    add_parser = AddNodeParser()

    add_parser.parse(ctx, '2 "for test reasons"')
    node = ctx.parent.find("div")

    assert node is not None
    assert node.get("class") == "test-class"
    assert node.text == "test add with value 2"

def test_user_overrides_render_block(md_gen, ctx):
    overrides = TemplateOverrides()
    overrides.actor_block = '<div class="test-class"><div class="actor">Actor "{{ name }}"</div></div>'

    md_gen(template_overrides=overrides)

    actor_parser = ActorBlockParser()

    actor_parser.begin(ctx, 'name="[[link|The Actor]]"')
    verify_is_dummy_block_element(ctx.parent)

    assert "name" in ctx.args.keys()
    assert ctx.args["name"] == "The Actor"

    actor_parser.finalize(ctx)

    outer_node = ctx.parent.find("div")

    assert outer_node is not None
    assert outer_node.get("class") == "test-class"

    inner_node = outer_node.find("div")
    assert inner_node is not None
    assert inner_node.text == 'Actor "The Actor"'

def test_user_overrides_disable_node(md_gen, ctx):
    overrides = TemplateOverrides()
    overrides.add = ''
    overrides.meter = '<div class="test-class">{{ meter_name }} {{ from }} to {{ to }}</div>'

    md_gen(template_overrides=overrides)

    add_parser = AddNodeParser()
    meter_parser = MeterNodeParser()

    add_parser.parse(ctx, '2 "for test reasons"')
    meter_parser.parse(ctx, '"test meter" from=5 to=3')

    # Verify only one div exists and it's the meter one
    nodes = ctx.parent.findall("div")
    assert len(nodes) == 1
    assert nodes[0].get("class") == "test-class"
    assert nodes[0].text == "test meter 5 to 3"

def test_user_overrides_disable_block(md_gen, ctx):
    overrides = TemplateOverrides()
    overrides.actor_block = ''

    md_gen(template_overrides=overrides)

    actor_parser = ActorBlockParser()

    actor_parser.begin(ctx, 'name="[[link|The Actor]]"')
    verify_is_dummy_block_element(ctx.parent)

    actor_parser.finalize(ctx)

    # Verify that with a disabled template, ctx.parent is still the dummy <div>
    verify_is_dummy_block_element(ctx.parent.find("div"))

def test_default_templates():
    data = {"block_name": "Test", "content": "test test test"}

    templater = Templater()
    assert templater.get_default_template("blocks").render(data).strip() == '<div class="ivm-block">Test: test test test</div>'
    assert templater.get_default_template("invalid").render(data).strip() == '<div></div>'

    templater = Templater(path="/random/nonexisting/path")
    assert templater.get_default_template("blocks").render(data).strip() == '<div></div>'
    assert templater.get_default_template("invalid").render(data).strip() == '<div></div>'


@pytest.mark.templater_no_init
def test_fallback_templater():
    default_templater = get_templater()

    assert default_templater is not None

    assert isinstance(default_templater.template_loader, PackageLoader)

    assert isinstance(default_templater.overrides, TemplateOverrides)
    assert default_templater.overrides.add is None

    assert default_templater.default_templates is not None
    assert default_templater.get_default_template("mechanics").render().strip() == '<div class="ivm-mechanics" role="note"></div>'

    # Verify calling get_templater() again yields the same instance
    assert get_templater() == default_templater

    # Verify get_templater() yields a new fallback instance after clearing it
    clear_templater()
    assert get_templater() != default_templater


def test_multiple_templater():
    overrides = TemplateOverrides(add='<div class="add-class">{{ add }}</div>')
    path = "tests/data/templates/"
    templater_one = Templater(overrides=overrides)
    templater_two = Templater(path=path)

    data = {"add": 2, "reason": "just because"}

    # Activate the first Templater instance
    set_templater(templater_one)
    assert get_templater() == templater_one

    # Get and parse the template, verify it's the user override
    template = get_templater().get_template("add", "nodes")
    assert template is not None
    assert template.render(data) == '<div class="add-class">2</div>'

    # Activate the second Templater instance
    set_templater(templater_two)
    assert get_templater() == templater_two

    # Verify it still renders the initial one at this point
    assert template.render(data) == '<div class="add-class">2</div>'

    # Get and parse the template again, verify it's now rendered from the templates
    template = get_templater().get_template("add", "nodes")
    # Note, if this fails, make sure the working directory is set to the project root, not tests/
    assert template is not None
    assert template.render(data).strip() == '<div class="templates-test">Add +2 just because</div>'

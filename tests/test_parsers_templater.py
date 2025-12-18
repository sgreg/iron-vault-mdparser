from jinja2 import Template

from ironvaultmd.parsers.blocks import ActorBlockParser
from ironvaultmd.parsers.nodes import AddNodeParser, MeterNodeParser
from ironvaultmd.parsers.templater import Templater, UserTemplates


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

    # Verify an unknown default type name will return None
    template = templater.get_template("unknown")
    assert template is None

    # Verify an unknown node name will return None
    template = templater.get_template("unknown", "nodes")
    assert template is None

    # Verify an unknown block type name will return a fallback template
    template = templater.get_template("unknown", "blocks")
    assert template is not None
    assert template.render() == Templater.block_fallback_template

def test_user_template_load():
    templater = Templater()

    user_templates = UserTemplates()
    user_templates.add = '<div class="test-class">test add</div>'
    user_templates.meter = '<div class="test-class">test meter</div>'
    user_templates.actor_block = '<div class="test-class"></div>'
    user_templates.mechanics_block = '<div class="test-class"></div>'

    templater.load_user_templates(user_templates)

    add_template = templater.get_template("add", "nodes")
    meter_template = templater.get_template("meter", "nodes")
    roll_template = templater.get_template("roll", "nodes")
    actor_template = templater.get_template("actor", "blocks")
    mechanics_template = templater.get_template("mechanics", "blocks")

    assert add_template.filename == "<template>"
    assert meter_template.filename == "<template>"
    assert roll_template.filename.endswith("/roll.html")
    assert actor_template.filename == "<template>"
    assert mechanics_template.filename == "<template>"


def test_user_template_render_node(md_gen, ctx):
    user_templates = UserTemplates()
    user_templates.add = '<div class="test-class">test add with value {{ add }}</div>'
    user_templates.actor_block = '<div class="test-class"><div class="actor">Actor {{ name }}</div></div>'

    md_gen(templates=user_templates)

    add_parser = AddNodeParser()
    assert add_parser.template.filename == "<template>"

    add_parser.parse(ctx, '2 "for test reasons"')
    node = ctx.parent.find("div")

    assert node is not None
    assert node.get("class") == "test-class"
    assert node.text == "test add with value 2"

def test_user_template_render_block(md_gen, ctx):
    user_templates = UserTemplates()
    user_templates.actor_block = '<div class="test-class"><div class="actor">Actor "{{ name }}"</div></div>'

    md_gen(templates=user_templates)

    add_parser = ActorBlockParser()
    assert add_parser.template.filename == "<template>"

    element = add_parser.begin(ctx, 'name="[[link|The Actor]]"')
    outer_node = ctx.parent.find("div")

    assert outer_node is not None
    assert outer_node.get("class") == "test-class"

    inner_node = outer_node.find("div")
    assert inner_node is not None
    assert inner_node.text == 'Actor "The Actor"'

def test_user_template_disable(md_gen, ctx):
    user_templates = UserTemplates()
    user_templates.add = ''
    user_templates.meter = '<div class="test-class">{{ meter_name }} {{ from }} to {{ to }}</div>'

    md_gen(templates=user_templates)

    add_parser = AddNodeParser()
    meter_parser = MeterNodeParser()

    assert add_parser.template is None
    assert meter_parser.template is not None

    add_parser.parse(ctx, '2 "for test reasons"')
    meter_parser.parse(ctx, '"test meter" from=5 to=3')

    # Verify only one div exists and it's the meter one
    nodes = ctx.parent.findall("div")
    assert len(nodes) == 1
    assert nodes[0].get("class") == "test-class"
    assert nodes[0].text == "test meter 5 to 3"

def test_user_template_disable_block(md_gen, ctx):
    user_templates = UserTemplates()
    user_templates.actor_block = ''

    md_gen(templates=user_templates)

    actor_parser = ActorBlockParser()

    # Verify fallback template was created for block parser
    assert actor_parser.template is not None
    assert actor_parser.template.render() == Templater.block_fallback_template

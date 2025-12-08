import logging

import pytest
from jinja2 import Template, TemplateNotFound

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


def test_user_template_render(md_gen, ctx):
    user_templates = UserTemplates()
    user_templates.add = '<div class="test-class">test add with value {{ add }}</div>'

    md_gen(templates=user_templates)

    add_parser = AddNodeParser()
    assert add_parser.template.filename == "<template>"

    add_parser.parse(ctx, '2 "for test reasons"')
    node = ctx.parent.find("div")

    assert node is not None
    assert node.get("class") == "test-class"
    assert node.text == "test add with value 2"

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

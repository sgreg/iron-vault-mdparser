import pytest
from jinja2 import Template, TemplateNotFound

from ironvaultmd.parsers.nodes import AddNodeParser
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

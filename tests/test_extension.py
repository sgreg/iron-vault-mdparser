import pytest
from markdown import Markdown

from ironvaultmd import IronVaultExtension
from ironvaultmd.parsers.templater import UserTemplates, get_templater, Templater, set_templater
from ironvaultmd.processors.links import Link


def test_extension_random_mechblock(md):
    # Some rough test to verify the parsing overall works okay enough.
    # This is most likely going to fail the tests sooner than later, but at least
    # breaking changes to regexes are likely going to be caught without checking
    # the actual parsed results in a browser.

    markdown = """```iron-vault-mechanics
move "[React Under Fire](datasworn:move:starforged\\/combat\\/react_under_fire)" {
    roll "Edge" action=6 adds=0 stat=2 vs1=6 vs2=1
    meter "Momentum" from=2 to=3
    meter "Spirit" from=4 to=2
}
- "in control"
```"""

    expected_html = """<div class="ivm-mechanics">
<div class="ivm-move ivm-move-result-strong">
<div class="ivm-move-name">React Under Fire</div>
<div class="ivm-roll ivm-roll-strong">
    Roll with
    <span class="ivm-roll-stat-name">Edge</span>:
    <span class="ivm-roll-action">6</span> +
    <span class="ivm-roll-stat">2</span> +
    <span class="ivm-roll-adds">0</span> =
    <span class="ivm-roll-score">8</span> vs
    <span class="ivm-roll-vs">6</span> |
    <span class="ivm-roll-vs">1</span>
    <span class="ivm-roll-outcome">strong</span>
</div>
<div class="ivm-meter ivm-meter-increase">
    <span class="ivm-meter-name">Momentum</span>:
    <span class="ivm-meter-diff">+1</span>
    <span class="ivm-meter-value">(2 &rarr; 3)</span>
</div>
<div class="ivm-meter ivm-meter-decrease">
    <span class="ivm-meter-name">Spirit</span>:
    <span class="ivm-meter-diff">-2</span>
    <span class="ivm-meter-value">(4 &rarr; 2)</span>
</div>
</div>
<div class="ivm-ooc">// in control</div>
</div>"""

    html = md.convert(markdown)
    assert html == expected_html


def test_extension_frontmatter(md_gen):
    markdown ="""---
key1: value1
key2: value2
---
Regular text
"""

    expected_frontmatter = {
        "key1": "value1",
        "key2": "value2",
    }

    expected_html = "<p>Regular text</p>"

    frontmatter = {}
    md_instance = md_gen(frontmatter=frontmatter)
    html = md_instance.convert(markdown)

    assert html == expected_html
    assert frontmatter == expected_frontmatter


def test_extension_frontmatter_invalid_type(md_gen):
    with pytest.raises(TypeError):
        frontmatter = "string"
        md_gen(frontmatter=frontmatter)

    with pytest.raises(TypeError):
        frontmatter = []
        md_gen(frontmatter=frontmatter)

    with pytest.raises(TypeError):
        frontmatter = ()
        md_gen(frontmatter=frontmatter)


def test_extension_links(md_gen):
    markdown = """# Some header

Some text with [[a link]] along a [[link|with label]].
    """

    links = []
    md_instance = md_gen(links=links)
    md_instance.convert(markdown)

    assert len(links) == 2

    assert isinstance(links[0], Link)
    assert links[0].ref == "a link"
    assert links[0].label == "a link"

    assert isinstance(links[1], Link)
    assert links[1].ref == "link"
    assert links[1].label == "with label"


def test_extension_links_invalid_type(md_gen):
    with pytest.raises(TypeError):
        links = "string"
        md_gen(links=links)

    with pytest.raises(TypeError):
        links = {}
        md_gen(links=links)

    with pytest.raises(TypeError):
        links = ()
        md_gen(links=links)


def test_extension_templates(md_gen):
    markdown = """```iron-vault-mechanics
add 2 "for a reason"
```"""
    user_templates = UserTemplates()
    user_templates.add = '<div class="test-class">test add with value {{ add }}</div>'

    md_instance = md_gen(templates=user_templates)
    html = md_instance.convert(markdown)

    assert '<div class="test-class">test add with value 2</div>' in html


def test_extension_templates_invalid(md_gen):
    markdown = """```iron-vault-mechanics
add 2 "for a reason"
```"""

    # Set invalid content as user-override templates
    md_instance = md_gen(templates={"ab": "cd"})
    html = md_instance.convert(markdown)

    # Verify the default nodes/add.html template is used
    assert '<div class="ivm-add">' in html


def test_extension_theme(md_gen):
    markdown = """```iron-vault-mechanics
add 2 "for a reason"
```"""

    # Generate md instance with an invalid theme directory
    md_instance = md_gen(theme="tests/data/theme")
    html = md_instance.convert(markdown)

    # Verify theme template is used
    assert '<div class="theme-test">Add +2 for a reason</div>' in html


def test_extension_theme_fail(md_gen):
    markdown = """```iron-vault-mechanics
add 2 "for a reason"
```"""

    # Generate md instance with an invalid theme directory
    md_instance = md_gen(theme="nonexisting/path")
    html = md_instance.convert(markdown)

    # Verify the default fallback template <div></div> is used
    assert html == "<div></div>"

    # Create user templates overrides to add alongside the invalid path
    user_templates = UserTemplates()
    user_templates.add = '<div class="test-class">test add with value {{ add }}</div>'

    md_instance = md_gen(theme="nonexisting/path", templates=user_templates)
    html = md_instance.convert(markdown)

    # Verify the user template override is used this time
    assert '<div class="test-class">test add with value 2</div>' in html


def test_extension_swap_theme(md_gen):
    markdown = """```iron-vault-mechanics
add 2 "for a reason"
```"""

    # Generate md instance with an invalid theme directory
    md_instance = md_gen(theme="tests/data/theme")

    template = get_templater().get_template("add", "nodes")
    # Note, if this fails, make sure the working directory is set to the project root, not tests/
    assert template is not None

    html = md_instance.convert(markdown)
    assert '<div class="theme-test">Add +2 for a reason</div>' in html

    # Create user templates overrides and create a new Templater instance with it
    user_templates = UserTemplates()
    user_templates.add = '<div class="test-class">test add with value {{ add }}</div>'
    templater = Templater(user_templates=user_templates)

    # Set the new Templater as the active one
    set_templater(templater)

    # Verify the existing Markdown instance now uses the user overrides
    html = md_instance.convert(markdown)
    assert '<div class="test-class">test add with value 2</div>' in html


def test_extension_full_features(md_gen):
    markdown = """---
key1: value1
key2: value2
---
Regular text with [[a link]], [[link|link with label]], [[link#anchor|link with anchor]]

```iron-vault-mechanics
move "[React Under Fire](datasworn:move:starforged\\/combat\\/react_under_fire)" {
    roll "Edge" action=6 adds=0 stat=2 vs1=6 vs2=1
    meter "Momentum" from=2 to=3
    meter "Health" from=5 to=4
}
- "in control"
```

More text
"""

    expected_links = [
        Link("a link", "", "a link"),
        Link("link", "", "link with label"),
        Link("link", "anchor", "link with anchor")
    ]

    expected_frontmatter = {
        "key1": "value1",
        "key2": "value2",
    }

    expected_html = """<p>Regular text with <span>a link (a link)</span>, <span>link with label (link)</span>, <span>link with anchor (link)</span></p>
<div class="ivm-mechanics">
<div class="ivm-move ivm-move-result-strong">
<div class="ivm-move-name">React Under Fire</div>
<div class="ivm-roll ivm-roll-strong">
    Roll with
    <span class="ivm-roll-stat-name">Edge</span>:
    <span class="ivm-roll-action">6</span> +
    <span class="ivm-roll-stat">2</span> +
    <span class="ivm-roll-adds">0</span> =
    <span class="ivm-roll-score">8</span> vs
    <span class="ivm-roll-vs">6</span> |
    <span class="ivm-roll-vs">1</span>
    <span class="ivm-roll-outcome">strong</span>
</div>
<div class="ivm-meter ivm-meter-increase">
    <span class="ivm-meter-name">Momentum</span>:
    <span class="ivm-meter-diff">+1</span>
    <span class="ivm-meter-value">(2 &rarr; 3)</span>
</div>
<div class="ivm-meter ivm-meter-decrease">
    <span class="ivm-meter-name">Health</span>:
    <span class="ivm-meter-diff">-1</span>
    <span class="ivm-meter-value">(5 &rarr; 4)</span>
</div>
</div>
<div class="my-ooc-class">(ooc: "in control")</div>
</div>
<p>More text</p>"""

    links = []
    frontmatter = {}

    user_templates = UserTemplates()
    user_templates.ooc = '<div class="my-ooc-class">(ooc: "{{ comment }}")</div>'
    user_templates.link = '<span>{{ label }} ({{ ref }})</span>'

    md_instance = md_gen(links=links, frontmatter=frontmatter, templates=user_templates)
    html = md_instance.convert(markdown)

    assert links == expected_links
    assert frontmatter == expected_frontmatter
    assert html == expected_html


def test_extension_reset(md_gen):
    markdown = """---
key1: value1
key2: value2
---
Regular text with [[a link]] and [[link|link with label]]
"""

    links = []
    frontmatter = {}

    md_instance = md_gen(links=links, frontmatter=frontmatter)
    md_instance.convert(markdown)

    assert len(links) == 2
    assert len(frontmatter) == 2

    md_instance.reset()

    assert len(links) == 0
    assert len(frontmatter) == 0


def test_extension_reset_none():
    markdown = """---
key1: value1
key2: value2
---
Regular text with [[a link]] and [[link|link with label]]
"""

    extension = IronVaultExtension(links=None, frontmatter=None)
    md_instance = Markdown(extensions=[extension])
    md_instance.convert(markdown)
    md_instance.reset()

    assert extension.frontmatter is None
    assert extension.links is None

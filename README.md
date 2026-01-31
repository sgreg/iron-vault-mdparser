# ironvaultmd - Iron Vault Markdown Parser
[![Quality Gate Status](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=alert_status&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)
[![Coverage](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=coverage&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)
[![Security Hotspots](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=security_hotspots&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)
[![Reliability Issues](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=software_quality_reliability_issues&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)
[![Maintainability Issues](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=software_quality_maintainability_issues&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)
[![Security Issues](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=software_quality_security_issues&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)

A [Python-Markdown](https://pypi.org/project/Markdown/) ([GitHub](https://github.com/Python-Markdown/markdown)) extension to parse Markdown files from the [Iron Vault](https://ironvault.quest/) ([GitHub](https://github.com/iron-vault-plugin/iron-vault)) Obsidian plugin.

The main idea for this extension is to convert Iron Vault Markdown journals into HTML sites for publishing.

## Features

Supports at this point
 - parsing ` ```iron-vault-mechanics ``` ` blocks
 - removing all other ` ```iron-vault-* ``` ` blocks
 - collecting frontmatter YAML information into a dictionary
 - regular and labeled wiki-style links, i.e. `[[link]]` and `[[link|label]]` (see also below for details)
 - user-definable templates for parsing the supported nodes

### Supported mechanics block content

> Disclaimer: This extension came into existence for my own purposes, to eventually publish my campaigns.
>
> After old-school pen and paper, and a bunch of other experiments, I eventually gave Iron Vault a try
> for my Starforged campaign at that time. This was in December 2024, around Iron Vault version 1.88.1.
>
> I have used it for other campaigns and Ironsworn rulesets since, but chances are I'm still missing some
> parts here or there, and full support for everything cannot be claimed yet. Nor any support for older
> Iron Vault versions.

#### Mechanics blocks and nodes
All nodes and blocks within a `iron-vault-mechanics` block should be supported.

Some have a strict regular expression to match, others support a generic `key=value` parameter matching,
with the latter hopefully covering some more variety in rulesets and Iron Vault versions.

#### Links
Links are detected and optionally collected into a list with their reference, anchor, and label,
see [the _Collecting Links_ section](#collecting-links) below.

Note that no actual linking is performed by default, and links are packed in a `<span class="ivm-link">`
element insted. This behavior can be changed by providing [template files](#template-files) or
[template overrides](#template-overrides) for the `link` element.

#### Roll results
Roll results of a move are collected, including dice rerolls and burning momentum, and
the outcome is added as CSS classes to the enclosing move block.

#### User-defined templates
Nodes are parsed using the [Jinja](https://jinja.palletsprojects.com/en/stable/) templating engine.
Every supported node has a default template and gets automatically passed all available data to it.

The default templates for each node (and some extra elements) along with a description of the available
variables can be found from the [`templates/` directory ](src/ironvaultmd/parsers/templates).

Each node template can be overridden when initiating the `IronVaultExtension`. See below for some examples.
Setting a template to an empty string (`''`) will prevent the node from being parsed to HTML altogether.

### Other Iron Vault bocks
All other [Iron Vault blocks](https://ironvault.quest/blocks/index.html) are removed.

Iron Vault renders these blocks to provide meaningful information, but from a Markdown file parsing
point of view, those are mostly just empty blocks with no extra data and no (straightforward) way
to fill in that data. So instead of showing empty blocks (are empty code block if e.g. the `FencedCode`
extension is used), they are just removed.

### Inline Mechanics
Iron Vault recently added [inline mechanics](https://ironvault.quest/other-features/inline-mechanics.html)
to display mechanics blocks within the regular text flow, instead of separate blocks.

There is currently no support for parsing those inline mechanics, nor any serious plans to add it.

It's in the back of my mind, but I prefer to wait until the feature has matured a bit and the mechanics
are fully documented before thinking of adding it.

### Other Obsidian features
Apart from the links and frontmatter, no other Obsidian-specific features are supported, or intended to
be added. Focus is primarily on the Iron Vault extension itself.

#### Callouts
Have a look at [`markdown-obsidian-callouts`](https://pypi.org/project/markdown-obsidian-callouts/)
([GitHub](https://github.com/lextoumbourou/markdown-obsidian-callouts)) for supporting Obsidian's
[callouts](https://help.obsidian.md/callouts). While not natively supported, it can also handle Iron Vault's
[spoiler callout](https://ironvault.quest/other-features/callouts.html).


## Installation

```sh
pip install ironvaultmd
```

This will install the required dependencies (`markdown`, `pyyaml`, and `Jinja2`) as well.

## Usage within Python code

Quick usage to convert an Iron Vault journal Markdown file to HTML and print it to the terminal:

```python
import markdown
from ironvaultmd import IronVaultExtension

md = markdown.Markdown(extensions=[IronVaultExtension()])

with open("/path/to/ironvault/Journals/JournalEntry.md", "r", encoding="utf-8") as file:
    print(md.convert(file.read()))
```

Check also the [`ironparser.py` example file](src/ironparser.py) for a more complete example to write a given journal Markdown file as HTML file.

### Collecting Links
```python
import markdown
from ironvaultmd import IronVaultExtension, Link

my_links: list[Link] = []
md = markdown.Markdown(extensions=[IronVaultExtension(links=my_links)])

with open("/path/to/ironvault/Journals/JournalEntry.md", "r", encoding="utf-8") as file:
    print(md.convert(file.read()))

print(my_links)
```

### Frontmatter
```python
import markdown
from ironvaultmd import IronVaultExtension

my_frontmatter = {}
md = markdown.Markdown(extensions=[IronVaultExtension(frontmatter=my_frontmatter)])

with open("/path/to/ironvault/Journals/JournalEntry.md", "r", encoding="utf-8") as file:
    print(md.convert(file.read()))

print(my_frontmatter)
```

### User Templates

#### Template Files
If you don't like the package-provided default templates, you can pass your own set of templates to the extension.

To make this work, you'll need a dedicated directory that resembles the default template directory layout:
```text
my-own-templates/
├── blocks
│   ├── actor.html
│   ├── block.html
│   ├── ...
├── link.html
└── nodes
    ├── add.html
    ├── burn.html
    ├── ...
```

Setting your own template directory:
```python
import markdown
from ironvaultmd import IronVaultExtension

md = markdown.Markdown(extensions=[IronVaultExtension(template_path="my-own-templates/")])
```

#### Template Overrides
Template files, both passed as a theme and default package-provided ones, can be overridden for additional flexibility.

This allows to either change the rendered text, by providing an alternative template string that Jinja understands,
or completely disable the specific template by setting it to an empty string `""`.

This is ideal if you're _mostly_ happy with the default templates but want to tweak a thing or two.

```python
import markdown
from ironvaultmd import IronVaultExtension, TemplateOverrides

my_overrides = TemplateOverrides()
my_overrides.add  = '<div class="my-own-class">Adding {{ add }}</div>'
my_overrides.roll = '<div class="ivm-roll">{{ total }} vs {{ vs1 }} and {{ vs2 }}</div>'
my_overrides.link = '<i>{{ label }}</i>'
my_overrides.xp = '' # don't add xp nodes to HTML output

md = markdown.Markdown(extensions=[IronVaultExtension(template_overrides=my_overrides)])
```

Note that you can provide both `template_path` and `template_overrides` values, and the overrides always take precedence over file-based templates.


## Usage with MkDocs

[MkDocs](https://www.mkdocs.org/) is a static site generator that creates HTML pages from Markdown files,
using [Python-Markdown](https://pypi.org/project/Markdown/) in the background. Since `ironvaultmd` is an
extension to just that, MkDocs can be used to create HTML pages from Iron Vault Markdown files.

See [the MkDocs getting started section](https://www.mkdocs.org/getting-started/) about setting it all up.

### Adding `ironvaultmd` support

Add `ironvaultmd` to your MkDocs project's `mkdocs.yml`:

```yaml
markdown_extensions:
  - ironvaultmd:IronVaultExtension
```

See https://www.mkdocs.org/user-guide/configuration/#markdown_extensions for more information.

### Templates

To set a [template files](#template-files) directory, modify the `mkdocs.yml` accordingly:

```yaml
markdown_extensions:
  - ironvaultmd:IronVaultExtension:
      template_path: "docs/themes/minimal/templates/"
```

**NOTE**:
1. Make sure you have the colon (`:`) added after `ironvaultmd:IronVaultExtension` if you add a `template_path`
2. The `template_path` directory must either be relative to the MkDocs project's root directory or an absolute path.
3. [Template overrides](#template-overrides) are unfortunately not supported

### Styles

```yaml
extra_css:
  - /themes/minimal/styles/layout/minimal.css
  - themes/minimal/styles/colors/muted.css
```

**NOTE**:
1. Unlike the templates directory, the `extra_css` directory is relative to the MkDocs project's `docs/` directory
2. Because of 1., paths can be with or without leading `/` as shown above. 

See https://www.mkdocs.org/user-guide/configuration/#extra_css for more information.


## Developing

See [`DEVELOPING.md`](DEVELOPING.md) for details on how to set up development environments etc. 

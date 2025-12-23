# ironvaultmd - Iron Vault Markdown Parser
[![Quality Gate Status](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=alert_status&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)
[![Coverage](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=coverage&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)
[![Security Hotspots](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=security_hotspots&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)
[![Reliability Issues](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=software_quality_reliability_issues&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)
[![Maintainability Issues](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=software_quality_maintainability_issues&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)
[![Security Issues](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=software_quality_security_issues&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)

A [Python-Markdown](https://pypi.org/project/Markdown/) ([GitHub](https://github.com/Python-Markdown/markdown)) extension to parse Markdown files from the [Iron Vault](https://ironvault.quest/) ([GitHub](https://github.com/iron-vault-plugin/iron-vault)) Obsidian plugin.

The main idea for this extension is to convert Iron Vault markdown journals into HTML sites for publishing.

## Features

Supports at this point
 - parsing ` ```iron-vault-mechanics ``` ` blocks (see [below](#supported-mechanics-block-content) for details)
 - collecting frontmatter YAML information into a dictionary
 - regular and labeled wiki-style links, i.e. `[[link]]` and `[[link|label]]` (see also below for details)
 - user-definable templates for parsing the supported nodes

### Supported mechanics block content

> Disclaimer: This extension came into existence for my own purposes, to eventually publish my campaigns.
>
> After old-school pen and paper, and a bunch of other experiments, I eventually gave Iron Vault a try for my most recent campaign - and I haven't looked back.
However, this only happened in December 2024, so somewhere around Iron Vault version 1.88.1, and only with a Starforged campaign.
Currently, neither journals created with an older version, nor OG Ironsworn, Delve, or Sundered Isles campaigns are supported,
and results may be disappointing.

#### Mechanics blocks and nodes
Currently supported blocks within a mechanics block:
actor, move, oracle-group, **oracle**, prompted oracle

Currently supported nodes within a mechanics block or any of the other blocks:
add, burn, **clock**, impact, initiative, meter, move, out-of-character comments,
**oracle**, position, **progress**, **progress-roll**, reroll, roll, **track**, xp.

Elements in **bold** support a generic key=value parameter in hopes to cover differences
in the game systems (and possible Iron Vault version compatibilities) better.

#### Links
Links are currently detected and optionally collected into a list with their reference and label,
but no actual linking is performed. To collect all found links:

By default, links are packed in a `<span class="ivm-link">` element, but a `link` user template string
can be defined to adjust that behavior - see the sections about templates for more information.

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

## Installation

```sh
pip install ironvaultmd
```

This will install the required dependencies, `markdown` and `pyyaml`, as well.

## Usage

Quick usage to convert an Iron Vault journal Markdown file to HTML and print it to the terminal:

```python
import markdown
from ironvaultmd import IronVaultExtension

md = markdown.Markdown(extensions=[IronVaultExtension()])

with open("/path/to/ironvault/Journals/JournalEntry.md", "r", encoding="utf-8") as file:
    print(md.convert(file.read()))
```

Check also the [`ironparser.py` example file](src/ironparser.py) for a more complete example to write a given journal Markdown file as HTML file.

### Links
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

This is ideal if you're _mostly_ happy with the default templates, but want to tweak a thing or two.

```python
import markdown
from ironvaultmd import IronVaultExtension, IronVaultTemplateOverrides

my_overrides = IronVaultTemplateOverrides()
my_overrides.add  = '<div class="my-own-class">Adding {{ add }}</div>'
my_overrides.roll = '<div class="ivm-roll">{{ total }} vs {{ vs1 }} and {{ vs2 }}</div>'
my_overrides.link = '<i>{{ label }}</i>'
my_overrides.xp = '' # don't add xp nodes to HTML output

md = markdown.Markdown(extensions=[IronVaultExtension(template_overrides=my_overrides)])
```

Note that you can provide both `template_path` and `template_overrides` values, and the overrides always take precedence over file-based templates.

## Developing

See [`DEVELOPING.md`](DEVELOPING.md) for details on how to set up development environments etc. 

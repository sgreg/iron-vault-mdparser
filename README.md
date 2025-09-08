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

#### Mechanics nodes
Currently supported nodes within a mechanics block:
add, burn, clock, initiative, meter, move, out-of-character comments,
oracle (note, only single oracle nodes, no oracle groups),
position, progress, progress-roll, reroll, roll, track.

#### Links
Links are currently detected and optionally collected into a list with their reference and label,
but no actual linking is performed. To collect all found links:

By default, links are packed in a `<span class="ivm-link">` element, but a `link` user template string
can be defined to adjust that behavior - see the sections about templates for more information.

#### User-defined templates
Nodes are parsed using the [Jinja](https://jinja.palletsprojects.com/en/stable/) templating engine.
Every supported node has a default template and gets automatically passed all available data to it.

The default templates for each node (and some extra elements) along with a description of the available
variables can be found from the [`templates/` directory ](src/ironvaultmd/parsers/templates).

Each node template can be overridden when initiating the `IronVaultExtension`. See below for some examples.

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
```python
import markdown
from ironvaultmd import IronVaultExtension, IronVaultTemplates

my_templates = IronVaultTemplates()
my_templates.add  = '<div class="my-own-class">Adding {{ add }}</div>'
my_templates.roll = '<div class="ivm-roll">{{ total }} vs {{ vs1 }} and {{ vs2 }}</div>'
my_templates.link = '<i>{{ label }}</i>'

md = markdown.Markdown(extensions=[IronVaultExtension(templates=my_templates)])
```

## Developing

See [`DEVELOPING.md`](DEVELOPING.md) for details on how to set up development environments etc. 

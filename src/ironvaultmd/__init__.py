r"""Iron Vault Markdown package root.

This package provides a Python‑Markdown extension and related helpers to
render Iron Vault/Obsidian‑style content:

- YAML front matter extraction
- Obsidian‑style wiki links (e.g., ``[[page#anchor|label]]``)
- Fenced mechanics blocks (```iron-vault-mechanics) parsed into structured
  HTML via Jinja templates

Public API
----------
- ``IronVaultExtension``: Main Markdown extension to register all processors.
- ``IronVaultTemplateOverrides``: Container to override/disable Jinja templates.
- ``FrontmatterException`` and ``MechanicsBlockException``: Error types raised
  by processors when encountering malformed input.
- ``Link``: Lightweight dataclass representing a collected wiki link.

Example:
    ```python
    from markdown import Markdown
    from ironvaultmd import IronVaultExtension, IronVaultTemplateOverrides

    links: list = []
    frontmatter: dict = {}
    overrides = IronVaultTemplateOverrides(  # override or disable templates if desired
        clock='<div class="ivm-clock">Clock {{ name }} activity happened</div>',  # skip the details
        ooc='<div class="my-own-ooc-class">{{ comment }}</div>',  # change to custom CSS class
        xp=''.  # don't render xp changes
    )

    md = Markdown(extensions=[
        IronVaultExtension(links=links, frontmatter=frontmatter, template_overrides=overrides)
    ])

    html = md.convert(
        "---\ntitle: Demo\n---\n\n,,,iron-vault-mechanics\n"
        "move \"[Face Danger](datasworn:move:...)\"\n"
        "roll \"edge\" action=4 adds=1 stat=2 vs1=3 vs2=8\n,,,"
    )
    ```

Attributes:
    __version__: Package version string.
    logger_name: Name of the package logger used throughout the codebase.
"""

__version__ = "0.4.0"
logger_name = "ironvaultmd"

from .ironvault import IronVaultExtension as IronVaultExtension
from .parsers.templater import TemplateOverrides as IronVaultTemplateOverrides
from .processors.frontmatter import FrontmatterException as FrontmatterException
from .processors.links import Link
from .processors.mechanics import MechanicsBlockException as MechanicsBlockException

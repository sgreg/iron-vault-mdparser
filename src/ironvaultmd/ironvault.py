"""Iron Vault Markdown extension integration.

This module exposes a Python‑Markdown `Extension` that wires together all
Iron‑Vault specific processors:

- Front matter extraction from YAML sections delimited by `---`.
- Obsidian‑style wiki links like `[[target#anchor|label]]`.
- Parsing of fenced mechanics blocks (```iron-vault-mechanics) into
  structured HTML via the parsers and Jinja templates.

Usage:
    ```python
    from markdown import Markdown
    from ironvaultmd.ironvault import IronVaultExtension

    links: list = []
    frontmatter: dict = {}

    md = Markdown(extensions=[
        IronVaultExtension(links=links, frontmatter=frontmatter)
    ])

    # Convert a small example document
    html = md.convert(
        "---\\ntitle: Demo\\n---\\n\\n,,,iron-vault-mechanics\\n"
        "move \"[Face Danger](datasworn:move:...)\"\\n"
        "roll \"edge\" action=4 adds=1 stat=2 vs1=3 vs2=8\\n,,,"
    )
    ```

Configuration keys accepted by the extension (can be passed as keyword
arguments when constructing `IronVaultExtension` or via Markdown config):

- `links` (list): Optional list that will be populated with parsed wiki links.
- `frontmatter` (dict): Optional dict that receives parsed YAML front matter.
- `templates` (UserTemplates): Optional overrides for Jinja templates.
"""
import logging

from markdown.extensions import Extension

from ironvaultmd import logger_name
from ironvaultmd.parsers.templater import UserTemplates, templater
from ironvaultmd.processors.frontmatter import IronVaultFrontmatterPreprocessor
from ironvaultmd.processors.links import WikiLinkProcessor
from ironvaultmd.processors.mechanics import (
    IronVaultMechanicsBlockProcessor,
    IronVaultMechanicsPreprocessor,
)

logger = logging.getLogger(logger_name)

class IronVaultExtension(Extension):
    """Markdown extension that registers the Iron‑Vault processors.

    Attributes:
        config: Python‑Markdown configuration mapping. Recognized keys are
            `links`, `frontmatter`, and `templates`.
        md: The `markdown.Markdown` instance after registration.
        links: Optional list that will collect parsed links.
        frontmatter: Optional dictionary that will receive parsed front matter.
    """
    def __init__(self, **kwargs):
        """Create and configure the Iron‑Vault Markdown extension.

        Args:
            **kwargs: Standard Python‑Markdown extension configuration. The
                following optional keys are recognized:
                - `links` (list): Collect parsed wiki links.
                - `frontmatter` (dict): Receive parsed YAML front matter.
                - `templates` (UserTemplates): Override/disable Jinja templates.

        Raises:
            TypeError: If `links` is provided but is not a list, or if
                `frontmatter` is provided but is not a dict.
        """

        self.config = {
            'links': [[], 'List of collected links'],
            'frontmatter': [{}, "YAML Frontmatter parsed into dictionary"],
            'templates': [UserTemplates(), "Node parser templates"],
        }

        super().__init__(**kwargs)

        self.md = None

        self.links = self.getConfig('links', None)
        if self.links is not None and not isinstance(self.links, list):
            raise TypeError("Parameter 'links' must be a list")

        self.frontmatter = self.getConfig('frontmatter', None)
        if self.frontmatter is not None and not isinstance(self.frontmatter, dict):
            raise TypeError("Parameter 'frontmatter' must be a dict")

        templates = self.getConfig('templates', UserTemplates())
        logger.debug(f"User templates given: {templates}")
        templater.load_user_templates(templates)


    def extendMarkdown(self, md) -> None:
        """Register processors on a `markdown.Markdown` instance.

        This wires up the preprocessor that normalizes mechanics fences, the
        front matter preprocessor, the mechanics block processor, and the wiki
        link inline processor. Processor priorities are chosen to ensure that
        mechanics blocks are isolated before fenced code runs, and that wiki
        links are handled before Markdown's own wikilinks extension.

        Args:
            md: The `markdown.Markdown` instance the extension is attached to.
        """
        md.registerExtension(self)
        self.md = md

        # fenced_code preprocessor has priority 25, ours must have higher one to make sure it's runs first
        md.preprocessors.register(IronVaultMechanicsPreprocessor(md), 'ironvault-mechanics-preprocessor', 50)
        md.preprocessors.register(IronVaultFrontmatterPreprocessor(md, self.frontmatter), 'ironvault-frontmatter-preprocessor', 40)
        md.parser.blockprocessors.register(IronVaultMechanicsBlockProcessor(md.parser), 'ironvault-mechanics', 175)
        # wikilinks extension processor has priority 75, so need to make sure ours has higher priority again
        md.inlinePatterns.register(WikiLinkProcessor(self.links), 'ironvault-wikilinks-inlineprocessor', 100)

    def reset(self) -> None:
        """Reset extension state between Markdown conversions.

        Clears the optional `links` and `frontmatter` containers if they have
        been provided, so each conversion starts with a clean state.
        """
        if self.links is not None:
            self.links.clear()
        if self.frontmatter is not None:
            self.frontmatter.clear()

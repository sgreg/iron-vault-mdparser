# Python-Markdown extension for iron-vault markdown blocks

"""
Convert iron-vault markdown blocks, such as iron-vault-mechanics to dedicated html css classes and whatnot .. dunno yet, let's see what else?
"""
import logging

from markdown.extensions import Extension

from ironvaultmd.parsers.base import UserTemplates, templater
from ironvaultmd.processors.frontmatter import IronVaultFrontmatterPreprocessor
from ironvaultmd.processors.links import WikiLinkProcessor
from ironvaultmd.processors.mechanics import (
    IronVaultMechanicsBlockProcessor,
    IronVaultMechanicsPreprocessor,
)

logger = logging.getLogger(__name__)

class IronVaultExtension(Extension):
    def __init__(self, **kwargs):

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
        md.registerExtension(self)
        self.md = md

        # fenced_code preprocessor has priority 25, ours must have higher one to make sure it's runs first
        md.preprocessors.register(IronVaultMechanicsPreprocessor(md), 'ironvault-mechanics-preprocessor', 50)
        md.preprocessors.register(IronVaultFrontmatterPreprocessor(md, self.frontmatter), 'ironvault-frontmatter-preprocessor', 40)
        md.parser.blockprocessors.register(IronVaultMechanicsBlockProcessor(md.parser), 'ironvault-mechanics', 175)
        # wikilinks extension processor has priority 75, so need to make sure ours has higher priority again
        md.inlinePatterns.register(WikiLinkProcessor(self.links), 'ironvault-wikilinks-inlineprocessor', 100)

    def reset(self) -> None:
        if self.links is not None:
            self.links.clear()
        if self.frontmatter is not None:
            self.frontmatter.clear()

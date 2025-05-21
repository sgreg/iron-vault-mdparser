# Python-Markdown extension for iron-vault markdown blocks

"""
Convert iron-vault markdown blocks, such as iron-vault-mechanics to dedicated html css classes and whatnot .. dunno yet, let's see what else?
"""
import logging

from markdown.extensions import Extension

from ironvaultmd.processors.frontmatter import IronVaultFrontmatterPreprocessor
from ironvaultmd.processors.mechanics import (
    IronVaultMechanicsBlockProcessor,
    IronVaultMechanicsPreprocessor,
)
from ironvaultmd.processors.links import WikiLinkProcessor

logger = logging.getLogger(__name__)

class IronVaultExtension(Extension):
    def extendMarkdown(self, md) -> None:
        md.registerExtension(self)
        self.md = md

        # fenced_code preprocessor has priority 25, ours must have higher one to make sure it's runs first
        md.preprocessors.register(IronVaultMechanicsPreprocessor(md), 'ironvault-mechanics-preprocessor', 50)
        md.preprocessors.register(IronVaultFrontmatterPreprocessor(md), 'ironvault-frontmatter-preprocessor', 40)
        md.parser.blockprocessors.register(IronVaultMechanicsBlockProcessor(md.parser), 'ironvault-mechanics', 175)
        # wikilinks extension processor has priority 75, so need to make sure ours has higher priority again
        md.inlinePatterns.register(WikiLinkProcessor(), 'ironvault-wikilinks-inlineprocessor', 100)

    def reset(self) -> None:
        self.md.Frontmatter = {}

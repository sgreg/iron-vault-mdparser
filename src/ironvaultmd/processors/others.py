"""Block processor for all other Iron Vault blocks."""

import re

from markdown.preprocessors import Preprocessor

from ironvaultmd.logger import logger


class IronVaultBlockException(Exception):
    """Raised when an Iron Vault block is malformed or inconsistent."""


#
# For a future improvement: combine with IronVaultMechanicsPreprocessor,
# so instead of running two preprocessors over the whole file, just transform
# the mechanics blocks and drop out all other Iron Vault blocks.
#


class IronVaultOtherBlocksPreprocessor(Preprocessor):
    """Markdown preprocessor for handling all non-mechanics blocks.

    These are all rendered within Obsidian, but mostly just empty blocks
    in Markdown itself. There isn't much use to render them, and without
    handling them at all, they may end up as code blocks if, for example,
    the FencedCode extension is enabled. So we just remove those completely.
    """

    START = re.compile(r"```iron-vault((?!-mechanics)\S*)")
    END = "```"

    def run(self, lines: list[str]) -> list[str]:
        """Drop all matching non-mechanics blocks.

        Args:
            lines: The Markdown document, split into lines.

        Returns:
            The Markdown document lines without non-mechanics blocks

        Raises:
            IronVaultBlockException: If nested mechanics blocks are detected.
        """
        inside = False
        new_lines = []

        for line_num, line in enumerate(lines):
            if self.START.match(line):
                if inside:
                    raise IronVaultBlockException("Starting block within block")
                inside = True

            elif inside:
                if line == self.END:
                    inside = False

            else:
                new_lines.append(line)

        logger.debug(new_lines)
        return new_lines

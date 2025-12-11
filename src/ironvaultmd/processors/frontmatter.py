r"""Front matter preprocessor for Iron Vault Markdown.

This module provides a Python-Markdown preprocessor that extracts YAML front
matter when a document starts with `---` and removes it from the Markdown
content. The parsed front matter can optionally be returned to the caller via
an external dictionary.

The preprocessor is designed to be registered on a `markdown.Markdown`
instance and run before other preprocessors which operate on the full text.

Example:
    ```python
    from markdown import Markdown
    from ironvaultmd.processors.frontmatter import IronVaultFrontmatterPreprocessor

    fm: dict = {}
    md = Markdown()
    md.preprocessors.register(IronVaultFrontmatterPreprocessor(md, fm), 'iv-frontmatter', 35)
    html = md.convert('---\ntitle: Test\n---\nContent')
    assert fm['title'] == 'Test'
    ```
"""

import yaml
from markdown import Markdown
from markdown.preprocessors import Preprocessor


class FrontmatterException(Exception):
    """Raised when a front matter section is malformed or incomplete."""


class IronVaultFrontmatterPreprocessor(Preprocessor):
    """Markdown preprocessor for handling Obsidian-style front matter.

    Front matter is optional YAML metadata located at the very beginning of a
    Markdown file and delimited by `---` lines. This preprocessor removes the
    section from the content and optionally parses it into a provided
    dictionary.

    Attributes:
        FRONTMATTER_DELIMITER: The string that delimits the YAML front matter
            section (default: `"---"`).
        frontmatter: Optional dictionary which, when provided, receives the
            parsed YAML key-value pairs.
    """
    FRONTMATTER_DELIMITER = "---"

    def __init__(self, md: Markdown | None = None, frontmatter: dict | None = None):
        """Create the preprocessor.

        Args:
            md: The `markdown.Markdown` instance this preprocessor is attached to.
                Can be `None` when instantiating before registration.
            frontmatter: Optional dictionary that will be populated with the
                parsed YAML front matter. If `None`, parsed data is discarded.

        Raises:
            TypeError: If `frontmatter` is provided but is not a `dict`.
        """
        if frontmatter is not None and not isinstance(frontmatter, dict):
            raise TypeError("Parameter 'frontmatter' must be a dict")

        super().__init__(md)
        self.frontmatter = frontmatter

    def run(self, lines: list[str]) -> list[str]:
        """Process the input lines and strip front matter if present.

        Args:
            lines: The Markdown document, split into lines.

        Returns:
            A list of lines with the front matter section removed when present.

        Raises:
            FrontmatterException: If the document starts with a front matter
                delimiter but no closing delimiter is found.
        """
        # Check if the very first line is the front matter delimiter, if not, do nothing.
        if lines[0] != self.FRONTMATTER_DELIMITER:
            # No frontmatter in file, return lines as is
            return lines

        # File has frontmatter
        # Remove first line containing the starting delimiter
        lines.pop(0)

        yaml_lines = []
        while lines:
            # Loop through markdown until ending delimiter is found,
            # move content from markdown to separate yaml_lines array.
            line = lines.pop(0)
            if line == self.FRONTMATTER_DELIMITER:
                # End of frontmatter, break out of the loop
                break
            yaml_lines.append(line)
        else:
            # Loop ended without finding frontmatter end delimiter.
            # This is kinda bad, but also means the file is misformated.
            raise FrontmatterException("Frontmatter ending delimiter not found")

        if self.frontmatter is not None:
            # If a frontmatter dictionary is set, create YAML data from the
            # extracted lines, parse it, and store it in that dictionary.
            yaml_text = '\n'.join(yaml_lines)
            frontmatter = yaml.safe_load(yaml_text)
            self.frontmatter.clear()
            self.frontmatter.update(frontmatter)

        return lines
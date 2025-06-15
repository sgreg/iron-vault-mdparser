import yaml
from markdown import Markdown
from markdown.preprocessors import Preprocessor


class FrontmatterException(Exception):
    pass


class IronVaultFrontmatterPreprocessor(Preprocessor):
    """Markdown preprocessor for handling Obsidian frontmatter data.

    Frontmatter data is optional metadata defined at the very beginning
    of the Markdown file, enclosed within '---' separators.
    This preprocessor checks if the processed content starts with that
    separator, and if so, collects everything until the closing separator
    internally, and removes it from the content itself.

    The collected frontmatter data can be stored in a given dictionary,
    and is that way available to the calling code, or alternatively can
    be just ignored (the default behavior if no dictionary is passed to
    its constructor)
    """
    FRONTMATTER_DELIMITER = "---"

    def __init__(self, md: Markdown | None = None, frontmatter: dict | None = None):
        if frontmatter is not None and not isinstance(frontmatter, dict):
            raise TypeError("Parameter 'frontmatter' must be a dict")

        super().__init__(md)
        self.frontmatter = frontmatter

    def run(self, lines: list[str]) -> list[str]:
        # Frontmatter information is YAML content at the very beginning of the file.
        # Check if the very first line is the frontmatter delimiter, if not, do nothing.
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
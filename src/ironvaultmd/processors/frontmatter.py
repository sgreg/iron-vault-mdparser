import yaml
from markdown.preprocessors import Preprocessor


class FrontmatterException(Exception):
    pass


class IronVaultFrontmatterPreprocessor(Preprocessor):
    """Markdown preprocessor for handling Obsidian frontmatter data.

    If the markdown content begins with `---`, all content until the closing
    pair of `---` is collected separately, removed from the markdown data itself,
    and parsed as YAML content. The resulting dictionary is then stored within
    the `md` instance as `md.Frontmatter`.
    """
    FRONTMATTER_DELIMITER = "---"

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

        # Create YAML content from extracted lines, parse it, and store internally
        yaml_text = '\n'.join(yaml_lines)
        frontmatter = yaml.safe_load(yaml_text)
        self.md.Frontmatter = frontmatter

        return lines
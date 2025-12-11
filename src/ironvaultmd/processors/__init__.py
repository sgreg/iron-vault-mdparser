r"""Custom Markdown processors for Iron Vault Markdown.

This package provides Python-Markdown processors that implement Iron Vault
Markdown features such as:

- Front matter extraction from YAML sections delimited by `---`.
- Obsidian-style wiki links like `[[target#anchor|label]]`.
- Parsing of mechanics blocks fenced by ```iron-vault-mechanics.

Processors can be registered on a `markdown.Markdown` instance via the
preprocessors, inline processors, or block processors registries.

Example:
    ```python
    from markdown import Markdown
    from ironvaultmd.processors.frontmatter import IronVaultFrontmatterPreprocessor

    md = Markdown()
    fm = {}
    md.preprocessors.register(IronVaultFrontmatterPreprocessor(md, frontmatter=fm), 'iv-frontmatter', 35)
    html = md.convert('---\nkey: value\n---\nContent\n')
    ```
"""

# iron-vault-mdparser

A [Python-Markdown](https://pypi.org/project/Markdown/) ([github](https://github.com/Python-Markdown/markdown)) extension to parse Markdown files from the [Iron Vault](https://ironvault.quest/) ([github](https://github.com/iron-vault-plugin/iron-vault)) Obsidian plugin.

Mainly parses anything within ` ```iron-vault-mechanics ... ``` ` blocks, but als frontmatter YAML.


## Usage

```python
$ python ./ironvault.py /path/to/vault/Journals/Session.md /tmp/Session.html
```

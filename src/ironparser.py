# Test the extension

import logging
import sys

import markdown
from markdown.extensions.fenced_code import FencedCodeExtension

from ironvaultmd import IronVaultExtension, IronVaultTemplates
from ironvaultmd.util import unhandled_nodes

logger = logging.getLogger("ironparser")

template_top = """<!-- Created by ironparser.py -->
<html>
<head>
<link rel="stylesheet" href="ironvault.css"
</head>
<body>
<div class="ivm-content">
"""

template_bottom = """
</div>
</body>
</html>"""

def read_markdown_file(md: markdown.Markdown, filename: str) -> str:
    with open(filename, "r", encoding="utf-8") as input_file:
        text = input_file.read()
    return md.convert(text)

def write_html_file(filename: str, html: str) -> int:
    with open(filename, "w", encoding="utf-8", errors="xmlcharrefreplace") as output_file:
        bytes_written = output_file.write(template_top)
        bytes_written += output_file.write(html)
        bytes_written += output_file.write(template_bottom)
        
    return bytes_written


infile = ""
outfile = ""
to_stdout = False

def usage():
    print("""Iron Vault Markdown Parser

Converts a markdown file to HTML, with special support for
markdown files created by Obsidian's iron-vault plugin.

Usage: python ironparser.py <infile> [<outfile>]

if outfile is omitted, <infile>.html is used
if outfile is "--", output is dumped to stdout instead
          """)

if __name__ == "__main__":
    # Add cmd line options
    #  - title, if unset use file name
    if len(sys.argv) == 3:
        infile = sys.argv[1]
        outfile = sys.argv[2]
        if outfile == "--":
            to_stdout = True
    elif len(sys.argv) == 2:
        if sys.argv[1] == "-h":
            usage()
            sys.exit(0)
        else:
            infile = sys.argv[1]
            outfile = infile + ".html"
    else:
        usage()
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)

    links = []
    frontmatter = {}
    templates = IronVaultTemplates()
    templates.progress = '<div class="ivm-progress">Progress for <b>{{ name }}</b> ({{ rank }}): {{ from }} &amp;rarr; {{ to }}</div>'

    markdown_extensions = [
        FencedCodeExtension(), # for parsing code blocks
        IronVaultExtension(links=links, frontmatter=frontmatter, templates=templates),
    ]
    md = markdown.Markdown(extensions=markdown_extensions)

    logger.info(f"Iron Vault Parser, {infile} -> {outfile}")

    logger.debug(f"Reading {infile}")
    html = read_markdown_file(md, infile)

    if to_stdout:
        print(html)
    else:
        size = write_html_file(outfile, html)
        logger.info(f"{size} bytes written to {outfile}")
    
    logger.debug(frontmatter)
    logger.debug(links)
    logger.debug(f"TODO: {sorted(unhandled_nodes)}")

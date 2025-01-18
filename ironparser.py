# Test the extension

import sys
import markdown
from markdown.extensions.wikilinks import WikiLinkExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from ironvault import IronVaultExtension, unhandled_nodes

from pprint import pprint
from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter


template_top = """<!-- Created by ironparser.py -->
<html>
<head>
<link rel="stylesheet" href="ironvault.css"
</head>
<body>
"""

template_bottom = """
</body>
</html>"""

def read_markdown_file(md: markdown.Markdown, filename: str) -> str:
    with open(filename, "r", encoding="utf-8") as input_file:
        text = input_file.read()
    html = md.convert(text)
    # return html
    formatter = HTMLFormatter(indent=4)
    return BeautifulSoup(html, 'html.parser').prettify(formatter=formatter)

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
markdown files created by Obisidian's iron-vault plugin.

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

    markdown_extensions = [
        WikiLinkExtension(base_url='/', end_url=''),
        FencedCodeExtension(),
        IronVaultExtension(),
    ]
    md = markdown.Markdown(extensions=markdown_extensions)

    print(f"Iron Vault Parser, {infile} -> {outfile}")

    print(f"Reading {infile}")
    html = read_markdown_file(md, infile)

    if to_stdout:
        print(html)
    else:
        size = write_html_file(outfile, html)
        print(f"{size} bytes written to {outfile}")
    
    pprint(md.Frontmatter)
    print(f"TODO: {sorted(unhandled_nodes)}")

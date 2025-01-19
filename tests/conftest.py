import pytest
import markdown
import xml.etree.ElementTree as etree
from ironvaultmd.ironvault import (
    IronVaultExtension,
    IronVaultFrontmatterPreprocessor,
    IronVaultMechanicsPreprocessor,
    IronVaultMechanicsBlockProcessor,
)


@pytest.fixture(name="md")
def markdown_instance():
    md = markdown.Markdown(extensions=[IronVaultExtension()])
    yield md


@pytest.fixture(name="frontproc")
def frontmatter_preprocessor(md):
    processor = IronVaultFrontmatterPreprocessor(md)
    yield processor


@pytest.fixture(name="mechproc")
def mechanics_block_preprocessor(md):
    processor = IronVaultMechanicsPreprocessor(md)
    yield processor


@pytest.fixture(name="mechblock")
def mechanics_block_blockprocessor(md):
    processor = IronVaultMechanicsBlockProcessor(md.parser)
    yield processor


@pytest.fixture(name="parent")
def parent_div_element():
    root = etree.ElementTree(etree.fromstring("<body></body>")).getroot()
    yield etree.SubElement(root, "div")

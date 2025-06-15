import xml.etree.ElementTree as etree

import markdown
import pytest

from ironvaultmd.ironvault import (
    IronVaultExtension,
)
from ironvaultmd.processors.frontmatter import IronVaultFrontmatterPreprocessor
from ironvaultmd.processors.mechanics import (
    IronVaultMechanicsBlockProcessor,
    IronVaultMechanicsPreprocessor,
)
from ironvaultmd.processors.links import WikiLinkProcessor


@pytest.fixture(name="md")
def markdown_instance():
    md = markdown.Markdown(extensions=[IronVaultExtension()])
    yield md


@pytest.fixture(name="frontproc")
def frontmatter_preprocessor(md):
    processor = IronVaultFrontmatterPreprocessor(md)
    yield processor


@pytest.fixture(name="frontproc_gen")
def frontmatter_preprocessor_generator(md):
    def _frontmatter_preprocessor(data_out_dict = None):
        return IronVaultFrontmatterPreprocessor(md, data_out_dict)
    return _frontmatter_preprocessor


@pytest.fixture(name="mechproc")
def mechanics_block_preprocessor(md):
    processor = IronVaultMechanicsPreprocessor(md)
    yield processor


@pytest.fixture(name="mechblock")
def mechanics_block_blockprocessor(md):
    processor = IronVaultMechanicsBlockProcessor(md.parser)
    yield processor


@pytest.fixture(name="linkproc")
def links_inlineprocessor():
    processor = WikiLinkProcessor()
    yield processor

@pytest.fixture(name="linkproc_gen")
def links_inlineprocessor_generator():
    def _links_inlineprocessor(data_out_list = None):
        return WikiLinkProcessor(data_out_list)
    return _links_inlineprocessor


@pytest.fixture(name="parent")
def parent_div_element():
    root = etree.ElementTree(etree.fromstring("<body></body>")).getroot()
    yield etree.SubElement(root, "div")

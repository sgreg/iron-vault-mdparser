import xml.etree.ElementTree as etree
from typing import Generator

import markdown
import pytest

from ironvaultmd.ironvault import (
    IronVaultExtension,
)
from ironvaultmd.parsers.context import Context, BlockContext, NameCollection
from ironvaultmd.parsers.templater import reset_templater, clear_templater
from ironvaultmd.processors.frontmatter import IronVaultFrontmatterPreprocessor
from ironvaultmd.processors.links import WikiLinkProcessor, LinkCollector
from ironvaultmd.processors.mechanics import (
    IronVaultMechanicsBlockProcessor,
    IronVaultMechanicsPreprocessor,
)
from ironvaultmd.processors.others import IronVaultOtherBlocksPreprocessor


@pytest.fixture(autouse=True)
def reset_templater_fixture(request: pytest.FixtureRequest):
    if "templater_no_init" in request.keywords:
        clear_templater()
    else:
        reset_templater()
    yield
    # Just in case, reset once more after the test
    reset_templater()


@pytest.fixture(name="md")
def markdown_instance():
    md = markdown.Markdown(extensions=[IronVaultExtension()])
    yield md


@pytest.fixture(name="md_gen")
def markdown_instance_generator(request):
    def _markdown_instance(**kwargs):
        return markdown.Markdown(extensions=[IronVaultExtension(**kwargs)])
    return _markdown_instance


@pytest.fixture(name="frontproc_gen")
def frontmatter_preprocessor_generator(md):
    def _frontmatter_preprocessor(data_out_dict = None):
        return IronVaultFrontmatterPreprocessor(md, data_out_dict)
    return _frontmatter_preprocessor


@pytest.fixture(name="othersproc")
def others_block_preprocessor(md):
    processor = IronVaultOtherBlocksPreprocessor(md)
    yield processor


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
    processor = WikiLinkProcessor(LinkCollector())
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


@pytest.fixture(name="ctx")
def parser_context(parent) -> Generator[Context]:
    context = Context(parent)
    yield context

@pytest.fixture(name="block_ctx")
def parser_content(ctx) -> Generator[Context]:
    block_parent = etree.SubElement(ctx.parent, "div")
    names = NameCollection("Test", "test", "test")
    block = BlockContext(names, block_parent, {}, {})
    ctx.push(block)
    yield ctx
import pytest

from ironvaultmd.parsers.base import (
    NodeParser,
    RegexNodeParser,
    SimpleContentNodeParser,
)


def test_parser_node(parent):
    node_name = "Node Test"
    parser = NodeParser(node_name)

    assert parser.node_name == node_name

    content = "Random Content"
    parser.parse(parent, content)

    node = parent.find("div")
    # Expects: <div class="ivm-node"><i>Node Test</i>: Random Content</div>
    assert node is not None
    assert "ivm-node" in node.get("class")
    assert node_name in node.text
    assert content in node.text


def test_parser_regex(parent):
    node_name = "Regex Test"
    parser = RegexNodeParser(node_name, "^.*$")

    assert parser.node_name == node_name
    assert parser.regex

    with pytest.raises(NotImplementedError):
        parser.parse(parent, "Random Content")

    assert parent.find("div") is None


def test_parser_simplecontent(parent):
    node_name = "SimpleContent Test"
    parser = SimpleContentNodeParser(node_name, "^.*$", ["testclass"])

    assert parser.node_name == node_name
    assert parser.regex

    with pytest.raises(NotImplementedError):
        parser.parse(parent, "Random Content")

    element = parent.find("div")
    assert element is not None
    assert not element.text

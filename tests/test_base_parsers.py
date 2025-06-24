from ironvaultmd.parsers.base import FallbackNodeParser


def test_parser_node(parent):
    node_name = "Node Test"
    parser = FallbackNodeParser(node_name)

    assert parser.node_name == node_name

    content = "Random Content"
    parser.parse(parent, content)

    node = parent.find("div")
    # Expects: <div class="ivm-node"><i>Node Test</i>: Random Content</div>
    assert node is not None
    assert "ivm-node" in node.get("class")
    assert node_name in node.text
    assert content in node.text

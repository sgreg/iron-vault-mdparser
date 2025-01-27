import pytest

from ironvaultmd.processors.mechanics import MechanicsBlockException


def test_mechblock_test_success(parent, mechblock):
    lines = [
        ",,,iron-vault-mechanics",
        "\n,,,iron-vault-mechanics",
        ",,,iron-vault-mechanics\n",
        "\n,,,iron-vault-mechanics\n",
        # these shouldn't actually happen?
        "content\n,,,iron-vault-mechanics\n",
        "\n,,,iron-vault-mechanics\ncontent",
        "content\n,,,iron-vault-mechanics\ncontent",
    ]

    for line in lines:
        assert mechblock.test(parent, line)


def test_mechblock_test_fail(parent, mechblock):
    lines = [
        "",
        "random other content",
        "random\nmultiline\nother\ncontent",
        ",,,iron-vault-mechanics-something",
        ",,,iron-vault-mechanics with more at the end",
        "```iron-vault-mechanics",
        "```",
    ]
    for line in lines:
        assert not mechblock.test(parent, line)


def test_mechblock_run_success(parent, mechblock):
    blocks_list = [
        [
            ",,,iron-vault-mechanics\nvalid content\n,,,",
        ],
        [
            ",,,iron-vault-mechanics\nvalid content\nmultiple lines\n\nand linebreaks\n,,,",
        ],
        [
            ",,,iron-vault-mechanics\nvalid content\nwith _all_ *kinds* ~of~ `other` **markdown** content\n,,,",
        ],
    ]

    for blocks in blocks_list:
        try:
            mechblock.run(parent, blocks)
        except MechanicsBlockException:
            pytest.fail("Unexpected MechanicsBlockException")


def test_mechblock_run_fail(parent, mechblock):
    blocks_list = [
        [
            # No ending tag
            ",,,iron-vault-mechanics\n",
        ],
        [
            # Ending tag not in same block
            ",,,iron-vault-mechanics\n",
            ",,,",
        ],
        [
            # Empty block (this should maybe be allowed and simply ignored?)
            ",,,iron-vault-mechanics\n,,,",
        ],
        [
            # Additional content before mechanics block, preprocessor should have removed that
            "before\n,,,iron-vault-mechanics\nvalid content\n,,,"
        ],
        [
            # Same but after the block
            "\n,,,iron-vault-mechanics\nvalid content\n,,,\nafter"
        ],
        [
            # Same but both before and after
            "before\n,,,iron-vault-mechanics\nvalid content\n,,,\nafter"
        ],
    ]

    for blocks in blocks_list:
        with pytest.raises(MechanicsBlockException):
            mechblock.run(parent, blocks)


def test_mechblock_parse_move(parent, mechblock):
    content = 'move "[Compel](datasworn link)" {\nadd 2\n}'
    mechblock.parse_content(parent, content)

    nodes = parent.findall("div")
    assert len(nodes) == 1

    node = nodes[0]
    assert "ivm-move" in node.get("class")
    assert node.find("div") is not None


def test_mechblock_parse_move_after_content(parent, mechblock):
    content = 'move "[Compel](datasworn link)" {\nadd 2\n}\nadd 2'
    mechblock.parse_content(parent, content)

    nodes = parent.findall("div")
    assert len(nodes) == 2

    assert "ivm-move" in nodes[0].get("class")
    assert "ivm-node" in nodes[1].get("class")


def test_mechblock_parse_node(parent, mechblock):
    mechblock.parse_content(parent, "add 2")

    node = parent.find("div")
    assert node is not None
    assert "ivm-node" in node.get("class")

    add = node.find("div")
    assert add is not None
    assert "ivm-add" in add.get("class")
    assert "add" in add.text.lower()


def test_mechblock_parse_ooc(parent, mechblock):
    mechblock.parse_content(parent, '- "comment comment comment"')

    node = parent.find("div")
    assert node is not None
    assert "ivm-ooc" in node.get("class")
    assert "comment comment comment" in node.text


def test_mechblock_parse_unknown(parent, mechblock):
    mechblock.parse_content(parent, "unknown")

    node = parent.find("div")
    assert node is None


def test_mechblock_parse_multiple(parent, mechblock):
    multiplier = 3

    content = "add 2\n" * multiplier
    mechblock.parse_content(parent, content)

    assert len(parent.findall("div")) == multiplier


def test_mechblock_parse_multiple_with_unknown(parent, mechblock):
    lines = [
        "add 2",
        # "unknown content", # this fails to fail at the moment
        "unknown",
        "add 1",
    ]

    content = "\n".join(lines)
    mechblock.parse_content(parent, content)

    assert len(parent.findall("div")) == 2

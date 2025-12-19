import xml.etree.ElementTree as etree

from ironvaultmd.parsers.context import Context, RollContext, RollResult


def test_context_stack(parent):
    ctx = Context(parent)

    assert len(ctx.blocks) == 0
    assert ctx.name == "root"
    assert ctx.roll is None

    root_element = ctx.parent # main mechanics block <div> created within Context() initialization

    # Create and push a new element
    element = etree.SubElement(ctx.parent, "div")
    ctx.push("test", element, {})
    # Verify there are 2 elements in the stack and 'parent' points to the new one
    assert len(ctx.blocks) == 1
    assert ctx.parent == element
    assert ctx.name == "test"
    assert ctx.roll is not None

    # Pop the stack and verify 'parent' is the mechanics block element again
    ctx.pop()
    assert len(ctx.blocks) == 0
    assert ctx.parent == root_element
    assert ctx.name == "root"
    assert ctx.roll is None

    # Make sure pop() won't remove the last element
    ctx.pop()
    assert len(ctx.blocks) == 0
    assert ctx.parent == root_element
    assert ctx.name == "root"
    assert ctx.roll is None

def test_context_properties(parent):
    ctx = Context(parent)

    assert ctx.parent == ctx.root
    assert ctx.name == "root"
    assert ctx.args is None
    assert ctx.roll is None

    element = etree.SubElement(ctx.parent, "div")
    ctx.push("test", element, {"key": "value"})

    assert ctx.parent == element
    assert ctx.name == "test"
    assert ctx.args is not None
    assert "key" in ctx.args.keys()
    assert ctx.args["key"] == "value"
    assert ctx.roll is not None

def test_context_replace_root(parent):
    ctx = Context(parent)

    original_root = ctx.root

    element_one = etree.SubElement(ctx.parent, "div")

    # Try to replace ctx root without a block in it, verify nothing will happen
    ctx.replace_root(element_one)
    assert ctx.parent == original_root

    # Push element, verify now it's the parent (but not the root)
    ctx.push("test", element_one, {})
    assert ctx.parent == element_one
    assert ctx.root == original_root

    # Create a second element and set a class attribute
    element_two = etree.SubElement(parent, "div")
    element_two.set("class", "test-class")

    # Verify ctx.parent is still the old, and it has no class attribute
    assert ctx.parent == element_one
    assert ctx.parent.get("class") is None

    # Do the root replacement
    ctx.replace_root(element_two)

    # Verify ctx.parent is now the new element with the set class attribute
    assert ctx.parent == element_two
    assert ctx.parent.get("class") == "test-class"


def test_rollcontext_roll():
    rctx = RollContext()

    data = [
        [(1, 2, 3, 4, 5), RollResult(6, 4, 5, "strong", False)],
        [(3, 0, 0, 3, 3), RollResult(3, 3, 3, "miss", True)],
        [(0, 2, 0, 9, 1), RollResult(2, 9, 1, "weak", False)],
        [(0, 0, 4, 3, 3), RollResult(4, 3, 3, "strong", True)],
        [(6, 4, 2, 10, 1), RollResult(10, 10, 1, "weak", False)], # verify that scope caps at 10
    ]

    for d in data:
        assert rctx.roll(*d[0]) == d[1]

        assert rctx.rolled == True
        assert rctx.momentum == 0
        assert rctx.progress == 0

def test_rollcontext_progressroll():
    rctx = RollContext()

    data = [
        [(6, 2, 3), RollResult(6, 2, 3, "strong", False)],
        [(3, 3, 3), RollResult(3, 3, 3, "miss", True)],
        [(5, 9, 1), RollResult(5, 9, 1, "weak", False)],
        [(4, 3, 3), RollResult(4, 3, 3, "strong", True)]
    ]

    for d in data:
        assert rctx.progress_roll(*d[0]) == d[1]

        assert rctx.rolled == True
        assert rctx.momentum == 0
        assert rctx.action == 0
        assert rctx.stat == 0
        assert rctx.adds == 0

def test_rollcontext_reroll():
    rctx = RollContext()

    res = rctx.roll(1, 2, 0, 4, 5)
    assert res == RollResult(3, 4, 5, "miss", False)
    assert rctx.reroll("action", 4) == RollResult(6, 4, 5, "strong", False)
    assert rctx.reroll("vs1", 6) == RollResult(6, 6, 5, "weak", False)
    assert rctx.reroll("vs2", 6) == RollResult(6, 6, 6, "miss", True)
    assert rctx.reroll("unknown", 6) == RollResult(6, 6, 6, "miss", True) # verify invalid die is ignored

    rctx = RollContext()

    res = rctx.progress_roll(6, 10, 9)
    assert res == RollResult(6, 10, 9, "miss", False)
    assert rctx.reroll("action", 2) == RollResult(6, 10, 9, "miss", False) # verify reroll of action die is ignored for progress-roll
    assert rctx.reroll("vs1", 3) == RollResult(6, 3, 9, "weak", False)
    assert rctx.reroll("vs2", 3) == RollResult(6, 3, 3, "strong", True)
    assert rctx.reroll("unknown", 3) == RollResult(6, 3, 3, "strong", True) # verify invalid die is ignored

def test_rollcontext_burn():
    rctx = RollContext()

    res = rctx.roll(1, 2, 0, 4, 5)
    assert res == RollResult(3, 4, 5, "miss", False)
    assert rctx.burn(8) == RollResult(8, 4, 5, "strong", False)

    rctx = RollContext()

    res = rctx.progress_roll(6, 8, 9)
    assert res == RollResult(6, 8, 9, "miss", False)
    assert rctx.burn(8) == RollResult(6, 8, 9, "miss", False) # verify progress roll ignores momentum burning

def test_rollcontext_value():
    rctx = RollContext()

    assert rctx.value("rolled") == False
    assert rctx.value("action") == 0
    assert rctx.value("stat") == 0

    rctx.roll(5, 2, 0, 1, 9)

    assert rctx.value("rolled") == True
    assert rctx.value("action") == 5
    assert rctx.value("stat") == 2

    assert rctx.value("") is None
    assert rctx.value("invalid") is None

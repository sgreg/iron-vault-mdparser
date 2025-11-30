from ironvaultmd.parsers.context import Context, RollContext, RollResult
from ironvaultmd.util import create_div


def test_context_stack(parent):
    ctx = Context(parent)

    assert len(ctx._elements) == 1
    assert ctx.parent == parent

    # Create and push a new element
    element = create_div(ctx.parent)
    ctx.push(element)
    # Verify there are 2 elements in the stack and 'parent' points to the new one
    assert len(ctx._elements) == 2
    assert ctx.parent == element

    # Pop the stack and verify 'parent' is the initial element again
    ctx.pop()
    assert len(ctx._elements) == 1
    assert ctx.parent == parent

    # Make sure pop() won't remove the last element
    ctx.pop()
    assert len(ctx._elements) == 1
    assert ctx.parent == parent


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

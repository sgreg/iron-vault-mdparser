from ironvaultmd.parsers.context import Context
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
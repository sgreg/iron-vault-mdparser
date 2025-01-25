import pytest

from ironvaultmd.processors.mechanics import MechanicsBlockException


def test_mechproc_dont_touch(mechproc):
    # Ensure any lines that don't contain ```iron-vault-mechanics block are left alone

    lines = [
        "test run that won't have any iron-vault-mechanics block",
        "expected behavior is the preprocessor won't do anything here",
        "",
        "```",
        "code that isn't iron-vault-mechanics block",
        "",
        "more inside that block",
        "```",
        "no newline will be added after the block either",
    ]

    assert mechproc.run(lines) == lines


def test_mechproc_convert_backticks(mechproc):
    # Ensure the backticks are converted to commas

    lines = [
        "```iron-vault-mechanics",
        "```",
    ]

    expected = [
        ",,,iron-vault-mechanics",
        ",,,",
    ]

    assert mechproc.run(lines) == expected


def test_mechproc_ignore_inline(mechproc):
    # Ensure iron-vault-mechanics starting tags are ignored if they're not the only content in a line

    lines = [
        "This is a line that mentiones ```iron-vault-mechanics inside some other content",
        "The parser should ignore this as well, also if it's at the beginning of the line",
        "```iron-vault-mechanics like this, but there's more text afterwards",
        "and neither if it's at the end of the lines ```iron-vault-mechanics",
    ]

    assert mechproc.run(lines) == lines


def test_mechproc_fail_double_start(mechproc):
    # Ensure another starting block within an already ongoing block will raise an Exception

    lines = [
        "```iron-vault-mechanics",
        "```iron-vault-mechanics",
        "```",
        "```",
    ]

    with pytest.raises(MechanicsBlockException):
        mechproc.run(lines)


def test_mechproc_newlines(mechproc):
    # Ensure newlines are added before (if there is content) and after the blocks,
    # and any newlines within the block are going to be removed

    lines = [
        "before",
        "```iron-vault-mechanics",
        "",
        "inside1",
        "",
        "",
        "inside2",
        "",
        "```",
        "after",
    ]

    expected = [
        "before",
        "",
        ",,,iron-vault-mechanics",
        "inside1",
        "inside2",
        ",,,",
        "",
        "after",
    ]

    assert mechproc.run(lines) == expected


def test_mechproc_ignore_missing_end(mechproc):
    # Ensure missing end tag doesn't cause an Exception and parsing works otherwise as expected

    lines = [
        "```iron-vault-mechanics",
        "inside",
        "",
        "end",
    ]

    expected = [
        ",,,iron-vault-mechanics",
        "inside",
        "end",
    ]

    try:
        processed = mechproc.run(lines)
        assert processed == expected
    except MechanicsBlockException:
        pytest.fail("Unexpected MechanicsBlockException")

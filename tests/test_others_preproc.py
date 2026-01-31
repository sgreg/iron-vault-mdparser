import pytest

from ironvaultmd.processors.others import IronVaultBlockException


def test_othersproc_dont_touch(othersproc):
    # Ensure any lines that don't contain ```iron-vault-* block are left alone

    lines = [
        "test run that won't have any iron-vault-xxx block",
        "expected behavior is the preprocessor won't do anything here",
        "",
        "```",
        "code that isn't iron-vault-xxx block",
        "",
        "more inside that block",
        "```",
        "no newline will be added after the block either",
        "and make extra sure now that",
        "",
        "```iron-vault-mechanics",
        "whatever is in here",
        "```",
        "",
        "won't be touched either",
    ]

    assert othersproc.run(lines) == lines


def test_othersproc_remove_valid(othersproc):
    # Ensure all non-mechanics blocks are removed

    lines = [
        "first line",
        "```iron-vault-character-info",
        "```",
        "```iron-vault-character-stats",
        "```",
        "```iron-vault-character-meters",
        "```",
        "```iron-vault-character-special-tracks",
        "```",
        "```iron-vault-character-impacts",
        "```",
        "```iron-vault-character-assets",
        "```",
        "```iron-vault-asset",
        "Starship",
        "```",
        "```iron-vault-clock",
        "```",
        "```iron-vault-moves",
        "```",
        "```iron-vault-oracles",
        "```",
        "```iron-vault-track",
        "```",
        "```iron-vault-truth",
        "truth:starforged/cataclysm",
        "inserted",
        "```",
        "```iron-vault-truth",
        "truth:starforged/exodus",
        "```",
        "```iron-vault-something-made-up",
        "```",
        "```iron-vault-",
        "```",
        "```iron-vault",
        "```",
        "last line",
    ]

    expected_lines = [
        "first line",
        "last line",
    ]

    assert othersproc.run(lines) == expected_lines


def test_othersproc_fail_double_start(othersproc):
    # Ensure another starting block within an already ongoing block will raise an Exception

    lines = [
        "```iron-vault-something",
        "```iron-vault-something-else",
        "```",
        "```",
    ]

    with pytest.raises(IronVaultBlockException):
        othersproc.run(lines)
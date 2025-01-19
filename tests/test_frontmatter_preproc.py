import pytest
from ironvaultmd import FrontmatterException


def test_frontproc_parse(frontproc):
    # Ensure intended overall behavior:
    #   - YAML content gets recognized and parsed
    #   - YAML content gets removed from input lines
    #   - Frontmatter dictionary within the Markdown instance has the parsed content

    lines = [
        "---",
        "key1: value1",
        "key2: value2",
        "---",
        "content"
    ]

    expected_lines = [
        "content"
    ]

    expected_dict = {
        "key1": "value1",
        "key2": "value2"
    }

    processed = frontproc.run(lines)
    assert processed == expected_lines
    assert frontproc.md.Frontmatter == expected_dict


def test_frontproc_ignore_later_lines(frontproc):
    # Ensure frontmatter is only parsed if the "---" delimiter is in the very first line
    # otherwise treat it just as regular content and ignore it

    lines = [
        "",
        "---",
        "key: value",
        "---",
        "content"
    ]

    processed = frontproc.run(lines)
    assert processed == lines
    assert frontproc.md.Frontmatter == {}


def test_frontproc_fail_no_end_delimiter(frontproc):
    # Ensure parsing fails with an Exception if frontmatter end delimited isn"t found

    lines = [
        "---",
        "key: value",
        "",
        "content"
    ]

    with pytest.raises(FrontmatterException):
        frontproc.run(lines)

    assert frontproc.md.Frontmatter == {}


def test_frontproc_empty_lines(frontproc):
    # Ensure empty lines are fine within frontmatter content

    lines = [
        "---",
        "",
        "key: value",
        "",
        "---"
    ]

    expected_dict = {
        "key": "value"
    }

    frontproc.run(lines)
    assert frontproc.md.Frontmatter == expected_dict


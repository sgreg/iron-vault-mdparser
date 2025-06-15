import pytest

from ironvaultmd.processors.frontmatter import FrontmatterException


def test_frontproc_parse(frontproc_gen):
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

    frontmatter = {}
    processor = frontproc_gen(frontmatter)
    processed = processor.run(lines)
    assert processed == expected_lines
    assert frontmatter == expected_dict


def test_frontproc_ignore_later_lines(frontproc_gen):
    # Ensure frontmatter is only parsed if the "---" delimiter is in the very first line
    # otherwise treat it just as regular content and ignore it

    lines = [
        "",
        "---",
        "key: value",
        "---",
        "content"
    ]

    frontmatter = {}
    processor = frontproc_gen(frontmatter)
    processed = processor.run(lines)
    assert processed == lines
    assert frontmatter == {}


def test_frontproc_fail_no_end_delimiter(frontproc_gen):
    # Ensure parsing fails with an Exception if frontmatter end delimited isn"t found

    lines = [
        "---",
        "key: value",
        "",
        "content"
    ]

    frontmatter = {}
    processor = frontproc_gen(frontmatter)

    with pytest.raises(FrontmatterException):
        processor.run(lines)

    assert frontmatter == {}


def test_frontproc_empty_lines(frontproc_gen):
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

    frontmatter = {}
    processor = frontproc_gen(frontmatter)
    processor.run(lines)
    assert frontmatter == expected_dict


def test_frontproc_no_dict(frontproc_gen):
    # Ensure passing None as dictionary doesn't cause a TypeError or other exception,
    # and removes the frontmatter from the Markdown content as usual.

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

    processor = frontproc_gen(None)
    processor.run(lines)
    processed = processor.run(lines)
    assert processed == expected_lines


def test_frontproc_invalid_dict(frontproc_gen):
    # Ensures that passing not a dictionary as frontmatter storage will cause TypeErrors

    with pytest.raises(TypeError):
        frontmatter = "string"
        frontproc_gen(frontmatter)

    with pytest.raises(TypeError):
        frontmatter = []
        frontproc_gen(frontmatter)

    with pytest.raises(TypeError):
        frontmatter = ()
        frontproc_gen(frontmatter)

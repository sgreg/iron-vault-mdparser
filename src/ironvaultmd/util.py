"""Utility helpers for Iron Vault Markdown processing.

This module contains small, focused helpers that are reused by processors and
parsers throughout the package. Functions are intentionally lightweight and
side‑effect free except for logging.

Provided utilities:
- String and regex helpers: `split_match`, `convert_link_name`.
- HTML convenience: `create_div` to build `etree` nodes with prefixed classes.
- Mechanics helpers: `check_dice`, `check_ticks`, `initiative_slugify`, `position_slugify`.
"""

import logging
import re
import xml.etree.ElementTree as etree

logger = logging.getLogger("ironvaultmd")


def split_match(text: str, match: re.Match[str]) -> tuple[str, str]:
    """Split a regex match into the text before and after the match.

    Args:
        text: The full source string that was searched with the regex.
        match: A successful regex match obtained from searching `text`.

    Returns:
        A tuple `(before, after)` containing the substrings before and after
        the matched span.
    """
    before = text[:match.start()]
    after = text[match.end():]
    return before, after


def create_div(parent: etree.Element, classes: list[str] | None = None) -> etree.Element:
    """Create a `<div>` element under `parent` with optional CSS classes.

    Each provided class name is automatically prefixed with `ivm-` to keep
    CSS naming consistent across the project.

    Args:
        parent: The parent HTML element to which the new div will be appended.
        classes: Optional list of CSS class identifiers without the `ivm-`
            prefix. Falsy values in the list are ignored.

    Returns:
        The created `etree.Element` representing the `<div>`.
    """
    e = etree.SubElement(parent, "div")

    if classes is not None:
        ivm_classes = ["ivm-" + c for c in classes if c]
        e.set("class", " ".join(ivm_classes))

    return e


RE_LINK_TEXT_MARKDOWN = re.compile(r"\[(?P<link_name>[^]]+)]\([^)]*\)")
RE_LINK_TEXT_WIKITYPE = re.compile(r"\[\[(?P<link_name>[^]|]+)]]")
RE_LINK_TEXT_WIKITYPE_NAMED = re.compile(r"\[\[[^]|]*\|(?P<link_name>[^]]+)]]")

def convert_link_name(raw: str) -> str:
    """Normalize a link‑decorated string to a plain display name.

    The function attempts to extract the human‑readable portion from either
    Markdown links like `[Text](url)` or Obsidian‑style wiki links such as
    `[[Page]]` or `[[Page|Label]]`. Escaped slashes (`\\/`) are unescaped.

    Args:
        raw: The original string possibly containing link markup.

    Returns:
        The normalized display string with link markup removed.
    """
    if (
        (m := RE_LINK_TEXT_MARKDOWN.search(raw)) or
        (m := RE_LINK_TEXT_WIKITYPE.search(raw)) or
        (m := RE_LINK_TEXT_WIKITYPE_NAMED.search(raw))
    ):
        link_name = m.groupdict()["link_name"].replace("\\/", "/")
        before, after = split_match(raw, m)
        return f"{before}{link_name}{after}"

    return raw.replace("\\/", "/")


def check_dice(score, vs1, vs2) -> tuple[str, bool]:
    """Derive hit/miss state and match flag from roll values.

    Args:
        score: The player score (action + stat + adds, capped at 10) or a
            progress/momentum value to compare against challenge dice.
        vs1: First challenge die value.
        vs2: Second challenge die value.

    Returns:
        A tuple `(hitmiss, match)` where `hitmiss` is one of `"strong"`,
        `"weak"`, or `"miss"`, and `match` indicates whether the challenge
        dice were a match.
    """
    if score > vs1 and score > vs2:
        hitmiss = "strong"
    elif score > vs1 or score > vs2:
        hitmiss = "weak"
    else:
        hitmiss = "miss"

    match = (vs1 == vs2)
    return hitmiss, match


def check_ticks(rank: str, current: int, steps: int) -> tuple[int, int]:
    """Compute ticks gained and new total for a progress track.

    Args:
        rank: The rank of the track to mark progress one. One of `"epic"`,
            "extreme"`, `"formidable"`, `"dangerous"`, or `"troublesome"`.
        current: The current number of ticks on the track.
        steps: Number of times to mark progress.

    Returns:
        A tuple `(ticks_gained, new_total_ticks)`.

    Notes:
        If `rank` is unknown, a warning is logged and `ticks_per_step` remains
        0; the total will then be unchanged.
    """
    ticks = 0
    match rank:
        case "epic":
            ticks = 1
        case "extreme":
            ticks = 2
        case "formidable":
            ticks = 4
        case "dangerous":
            ticks = 8
        case "troublesome":
            ticks = 12
        case _:
            logger.warning(f"Fail to check ticks, unknown rank {rank}")

    return ticks * steps, min(current + (ticks * steps), 40)


def initiative_slugify(initiative: str) -> str | None:
    """Convert an initiative state to a CSS‑friendly slug.

    Args:
        initiative: Human‑readable initiative state, e.g., "has initiative".

    Returns:
        A slug string such as `"nocombat"`, `"initiative"`, or `"noinitiative"`.
        Returns `None` for unknown values (and logs a warning).
    """
    match initiative:
        case "out of combat":
            return "nocombat"
        case "has initiative":
            return "initiative"
        case "no initiative":
            return "noinitiative"

    logger.warning(f"Unhandled initiative '{initiative}'")
    return None


def position_slugify(position: str) -> str | None:
    """Convert a position state to a CSS‑friendly slug.

    Args:
        position: Human‑readable position state, e.g., "in control".

    Returns:
        A slug string such as `"nocombat"`, `"control"`, or `"badspot"`.
        Returns `None` for unknown values (and logs a warning).
    """
    match position:
        case "out of combat":
            return "nocombat"
        case "in control":
            return "control"
        case "in a bad spot":
            return "badspot"

    logger.warning(f"Unhandled position '{position}'")
    return None

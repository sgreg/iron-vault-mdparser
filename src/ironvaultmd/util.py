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

from ironvaultmd import logger_name

logger = logging.getLogger(logger_name)


def split_match(text: str, match: re.Match[str]) -> tuple[str, str]:
    """Split a regex match into the text before and after the match.

    Args:
        text: The full source string that was searched with the regex.
        match: A successful regex match obtained from searching `text`.

    Returns:
        A tuple `(before, after)` containing the substrings before and after
        the matched span.
    """
    before = text[: match.start()]
    after = text[match.end() :]
    return before, after


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
        (m := RE_LINK_TEXT_MARKDOWN.search(raw))
        or (m := RE_LINK_TEXT_WIKITYPE.search(raw))
        or (m := RE_LINK_TEXT_WIKITYPE_NAMED.search(raw))
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

    match = vs1 == vs2
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


def ticks_to_progress(total_ticks: int) -> tuple[int, int]:
    """Convert a total number of ticks into full boxes and remaining ticks.

    Note that the function assumes the given `total_ticks` is a valid value,
    no limitations are performed, and values above 10 boxes can be returned.

    Args:
        total_ticks: Number of ticks to convert, e.g., one of the return
            values retrieved from `check_ticks()`.

    Returns:
        A tuple `(boxes, ticks)`
    """
    boxes = int(total_ticks / 4)
    ticks = total_ticks - (boxes * 4)

    return boxes, ticks


def ticks_to_float(total_ticks: int) -> float:
    """Convert a total number of ticks into a floating point representation.

    Note that the function assumes the given `total_ticks` is a valid value,
    no limitations are performed, and values above 10.0 can be returned.

    Args:
        total_ticks: Number of ticks to convert, e.g., one of the return
            values retrieved from `check_ticks()`.

    Returns:
        Float value, e.g. 1.75 for 1 box and 3 ticks.
    """
    progress = ticks_to_progress(total_ticks)
    return progress[0] + (progress[1] * 0.25)


def initiative_slugify(initiative: str) -> str:
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
    return "unknown"


def position_slugify(position: str) -> str:
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
    return "unknown"

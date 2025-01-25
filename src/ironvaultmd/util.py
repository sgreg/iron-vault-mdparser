import re
import xml.etree.ElementTree as etree


def split_match(text: str, match: re.Match[str]) -> tuple[str, str]:
    """Split a regex match to extract and return any text before and after the match"""
    before = text[:match.start()]
    after = text[match.end():]
    return (before, after)


def create_div(parent: etree.Element, classes: list[str] | None = None) -> etree.Element:
    """Create and return an etree.Element `<div>` with an optional list of class identifiers"""
    e = etree.SubElement(parent, "div")

    if classes is not None:
        ivm_classes = ["ivm-" + c for c in classes if c]
        e.set("class", " ".join(ivm_classes))

    return e


unhandled_nodes: list[str] = []
def add_unhandled_node(node: str) -> None:
    """Keep track of iron-vault-mechanics nodes that aren't handled yet (for dev purpose only)"""
    if node not in unhandled_nodes:
        unhandled_nodes.append(node)


def check_dice(score, vs1, vs2) -> tuple[str, bool]:
    """Check dice values against each other and return hit/miss and match situation of it"""
    if score > vs1 and score > vs2:
        hitmiss = "strong"
    elif score > vs1 or score > vs2:
        hitmiss = "weak"
    else:
        hitmiss = "miss"

    match = (vs1 == vs2)
    return (hitmiss, match)


def check_ticks(rank: str, current: int, steps: int) -> int:
    """Check and return new progress track ticks value"""
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
            print(f"Fail to check ticks, unknown rank {rank}")
            return current

    return current + (ticks * steps)
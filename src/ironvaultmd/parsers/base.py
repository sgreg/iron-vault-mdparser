"""Base classes for Iron Vault mechanics parsers.

This module defines abstract helpers used by concrete parsers in
`ironvaultmd.parsers.blocks` and `ironvaultmd.parsers.nodes`.

- `NodeParser` implements a small framework for single-line node parsers that
  match input using a compiled regular expression and optionally render output
  using a Jinja template.
- `MechanicsBlockParser` provides a similar framework for higher-level block
  parsers that own a subtree in the output document.
"""

import logging
import re
import xml.etree.ElementTree as etree
from typing import Any

from jinja2 import Template

from ironvaultmd import logger_name
from ironvaultmd.parsers.context import Context
from ironvaultmd.parsers.templater import templater

logger = logging.getLogger(logger_name)


class NodeParser:
    """Base class for single-line mechanics node parsers.

    Subclasses should provide a `regex` pattern describing the accepted input
    for a node and may override `create_args` to transform captured values into
    template arguments. If a template with the same name exists, the parsed
    node will be rendered and appended to the current parent element.

    Attributes:
        node_name: Human-readable name of the node (also used to load the
            default template via the `Templater`).
        regex: Compiled regular expression used to match a node line.
        template: Jinja `Template` resolved for `node_name`, or `None` if no
            template is available.
    """
    node_name: str
    regex: re.Pattern[str]
    template: Template | None

    def __init__(self, name: str, regex: str) -> None:
        """Initialize the node parser.

        Args:
            name: Display name for the node (used for template lookup).
            regex: Regular expression string for matching input lines.
        """
        self.node_name = name
        self.regex = re.compile(regex)
        self.template = templater.get_template(name, "nodes")

    def _match(self, data: str) -> dict[str, str | Any] | None:
        """Try to match input text and return a group dictionary.

        Args:
            data: Node parameters string/

        Returns:
            A dict of named regex groups if the pattern matches; otherwise `None`.
        """
        match = self.regex.search(data)

        if match is None:
            logger.warning(f"Fail to match parameters for {self.node_name}: {repr(data)}")
            return None

        logger.debug(match)
        return match.groupdict()

    def parse(self, ctx: Context, data: str) -> None:
        """Parse a node line and append rendered output if applicable.

        This is handled by dedicated subclasses specific to a node name.
        The node name itself is therefore not part of the `data` string,
        only its parameters.

        Rendered output is appended directly to the parent HTML element
        stored within the passed `Context`.

        Args:
            ctx: Current parsing `Context`.
            data: Node parameters string.
        """
        template = self.template
        matches = self._match(data)
        if matches is None:
            # Use generic node template as fallback, showing data as-is
            template = templater.get_template("node", "nodes")
            args = {"node_name": self.node_name, "content": data}

        else:
            args = self.create_args(matches, ctx)

        if template is not None:
            out = template.render(args)
            ctx.parent.append(etree.fromstring(out))

    def create_args(self, data: dict[str, str | Any], _: Context) -> dict[str, str | Any]:
        """Build template arguments from regex groups.

        Subclasses override this to post-process captured values or to add
        context-derived information.

        Args:
            data: Named regex groups captured from the input line.
            _: The current parsing `Context` (unused by the base implementation).

        Returns:
            A dictionary that will be passed to the Jinja template as context.
        """
        return data


class MechanicsBlockParser: # there's already a BlockParser in Markdown itself, so let's just best use another name
    """Base class for mechanics block parsers.

    Block parsers own a subtree in the output and typically span multiple
    lines. They create a root element in `begin`, may add additional content as
    nodes are parsed, and can perform finalization in `finalize`.

    Attributes:
        block_name: Human-readable name of the block.
        regex: Compiled pattern used to match and extract parameters from the
            block's opening line.
        template: Jinja `Template` resolved for `block_name`, or `None` if no
            template is available.
    """
    def __init__(self, name:str, regex: str, template_name:str | None = None):
        """Create the block parser.

        Args:
            name: Display name for the block
            regex: Regular expression string for the opening line.
            template_name: Optional template name, falls back to the block name
        """
        self.block_name = name
        self.regex = re.compile(regex)
        if template_name is None:
            template_name = name
        self.template = templater.get_template(template_name, "blocks")

    def _match(self, data: str) -> dict[str, str | Any] | None:
        """Try to match the block opening line and return a group dictionary.

        Args:
            data: Raw block parameter string.

        Returns:
            A dict of named regex groups if the pattern matches; otherwise `None`.
        """
        match = self.regex.search(data)

        if match is None:
            logger.warning(f"Fail to match parameters for block {self.block_name}: {repr(data)}")
            return None

        logger.debug(match)
        return match.groupdict()

    def begin(self, ctx: Context, data: str) -> tuple[etree.Element, dict[str, Any]]:
        """Create and return the block's root element and its arguments.

        Matches the block's opening line with the parser's `regex` and
        builds an argument dictionary from its match groups.

        If the opening line cannot be matched, a generic block element is
        created containing a textual representation of the original input.

        Args:
            ctx: Current parsing `Context`.
            data: Block parameter string from the opening line.

        Returns:
            A tuple (`element`, `args`) containing the newly created HTML
            element which becomes the current parent in the context stack,
            and a dictionary of its parsed arguments.
        """
        matches = self._match(data)
        if matches is None:
            self.template = templater.get_template("block", "blocks")
            args = {"block_name": self.block_name, "content": data}
        else:
            args = self.create_args(matches)

        # Don't bother with templates yet, finalize() will handle that,
        # we just need a container at this point
        element = etree.SubElement(ctx.parent, "div")

        return element, args

    def create_args(self, data: dict[str, str | Any]) -> dict[str, str | Any]:
        """Build template arguments from regex groups.

        Subclasses override this to post-process captured values or to add
        context-derived information.

        Args:
            data: Named regex groups captured from the input line.
            _: The current parsing `Context` (unused by the base implementation).

        Returns:
            A dictionary that will be passed to the Jinja template as context.
        """
        return data

    def finalize(self, ctx):
        """Finalize the block after all nested nodes have been parsed.

        Renders the template with its parsed arguments (found in `ctx.args`)
        and replaces the block's temporary `<div>` container parent with it.

        Calls `finalize_args()` which subclasses may override to add more
        args data to their templates.

        Args:
            ctx: Current parsing `Context`.
        """
        if self.template is None:
            # Do nothing, the block is already in a dummy <div>,
            # just keep it that way.
            return

        args = self.finalize_args(ctx)
        new_root = etree.fromstring(self.template.render(args))
        ctx.replace_root(new_root)

    def finalize_args(self, ctx: Context) -> dict[str, Any]:
        """Extend template arguments during finalization.

        Called right before rendering the template to optionally extend
        the initial args parsed in `begin()` with additional data.

        Subclasses may override this method, otherwise the initial args
        are returned as-is.

        Args:
            ctx: Current parsing `Context`.

        Returns:
            A dictionary that will be passed to the Jinja template as context.
        """
        return ctx.args

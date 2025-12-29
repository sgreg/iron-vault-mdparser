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

from ironvaultmd import logger_name
from ironvaultmd.parsers.context import Context, BlockContext, NameCollection
from ironvaultmd.parsers.templater import get_templater

logger = logging.getLogger(logger_name)


class Parser:
    """Base class for all mechanics parsers.

    Provides common functionality for matching input against a regex pattern
    and optionally parsing key=value parameters from the matched groups.

    Attributes:
        names: Name collection of the parser, used for logging and lookup.
        input_regex: Compiled regular expression used to match input.
        extra_regex: Optional compiled regex for parsing key=value pairs.
    """
    names: NameCollection
    input_regex: re.Pattern[str]
    extra_regex: re.Pattern[str] | None

    def __init__(self, names: NameCollection, line_regex: str, param_regex: str | None = None) -> None:
        """Initialize the parser.

        Args:
            names: Name collection of the parser.
            line_regex: Regular expression string for matching input.
            param_regex: Optional regex for parsing individual key=value parameters.
        """
        self.names = names
        self.input_regex = re.compile(line_regex)
        self.extra_regex = re.compile(param_regex) if param_regex else None

    def _match(self, data: str) -> dict[str, Any] | None:
        """Try to match input text and return a group dictionary.

        Args:
            data: Input string to match against.

        Returns:
            A dict of named regex groups if the pattern matches; otherwise `None`.
        """
        match = self.input_regex.search(data)

        if match is None:
            logger.warning(f"Failed to match parameters for {self.names.name}: {repr(data)}")
            return None

        logger.debug(f"{self.names.name} match: {match}")
        return self._parse_params(match.groupdict())

    # noinspection PyMethodMayBeStatic
    def _parse_params(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse parameters from matched groups.

        Intended for the `ParameterParsingMixin` to split key=value
        parameters into a dictionary.

        Args:
            data: Dictionary of regex groups from the initial match.

        Returns:
            Processed dictionary, by default, returns data as-is.
        """
        return data

    def handle_args(self, data: dict[str, Any], _: Context) -> dict[str, Any]:
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


class ParameterParsingMixin:
    """Mixin that provides key=value parameter parsing functionality.

    Classes using this mixin must have:
    - param_regex: Compiled regex for parsing key=value pairs
    - known_keys: List of expected parameter names
    - names: Parser name collection (for logging).

    Attributes:
        PARAMS_REGEX: Pattern matching the entire parameter string.
        PARAM_REGEX: Pattern for extracting individual key=value pairs.
    """
    PARAMS_REGEX = r'^(?P<params>(?:[\w-]+=(?:"[^"]*"|\d+|true|false)(?:\s+|$))+)$'
    PARAM_REGEX = r'([\w-]+)=((?:"[^"]*"|\d+|true|false))'

    extra_regex: re.Pattern[str]
    known_keys: list[str]
    names: NameCollection

    def _parse_params(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse key=value pairs and separate known from unknown parameters.

        Returns a dict with the parameters, plus an extra `data["extra"]`
        entry containing a dict of all the extra, unknown parameters.

        Args:
            data: Dictionary containing a 'params' string with key=value pairs.

        Returns:
            Dictionary with parsed parameters
        """
        params_string = data.get('params', '')
        params = {}

        # Convert parameter types
        for key, value in self.extra_regex.findall(params_string):
            if value.startswith('"') and value.endswith('"'):
                params[key] = value[1:-1]
            elif value.isdigit():
                params[key] = int(value)
            elif value in ('true', 'false'):
                params[key] = value == 'true'
            else:
                logger.warning(f"Unexpected param match in {self.names.name}: {value}")

        # Separate known from unknown parameters
        known = {}
        extra = {}

        for key, value in params.items():
            if key in self.known_keys:
                known[key] = value
            else:
                extra[key] = value

        known["extra"] = extra

        logger.debug(f"Parsed params for {self.names.name}: {known}")
        return known


class NodeParser(Parser):
    """Base class for single-line mechanics node parsers.

    Subclasses should provide a `regex` pattern describing the accepted input
    for a node and may override `create_args` to transform captured values into
    template arguments. A "nodes" type template of the same name as provided
    is looked up during parsing.
    """

    def parse(self, ctx: Context, data: str) -> None:
        """Parse a node line and append rendered output if applicable.

        This is handled by dedicated subclasses specific to a node name.
        The node name itself is therefore not part of the `data` string,
        only its parameters.

        If the line matches the parser's `line_regex`, the node's template
        is looked up from the active `Templater`, otherwise the default
        node fallback template is used.

        If the template lookup returns `None`, nothing is rendered.
        Otherwise, the rendered output is appended directly to the
        parent HTML element stored within the passed `Context`.

        Args:
            ctx: Current parsing `Context`.
            data: Node parameters string.
        """
        matches = self._match(data)
        if matches is None:
            # Use the fallback node template, showing data as-is
            logger.debug(f"Using fallback template for {self.names.name} node")
            template = get_templater().get_default_template("nodes")
            args = {"node_name": self.names.name, "content": data}

        else:
            template = get_templater().get_template(self.names.template, "nodes")
            args = self.handle_args(matches, ctx)

        logger.debug(f"Arranged args for {self.names.name}: {args}")

        if template is not None:
            out = template.render(args)
            ctx.parent.append(etree.fromstring(out))


class ParameterNodeParser(ParameterParsingMixin, NodeParser):
    """Node parser that uses the generic key=value parameter mechanism.

    Automatically parses parameters in the format:
        `key1=value1 key2="value2" ...`
    Separates known from unknown parameters and provides a dict containing
    the parsed known parameters along an `extra` entry with a dict of the
    unknown parameters to the `handle_args()` method.

    Known keys must be provided in the constructor.

    Note that defining a key as known only defined that it _can_ be expected
    in the parsed line, not that it _must_ be there. If a known key isn't
    found, it's simply omitted from the collected args dict.

    Attributes:
        known_keys: List of expected parameter names.
    """
    known_keys: list[str]

    def __init__(self, names: NameCollection, keys: list[str]) -> None:
        """Initialize with a list of expected parameter keys.

        Args:
            names: Name collection for the node.
            keys: List of known/expected parameter names.
        """
        super().__init__(names, ParameterParsingMixin.PARAMS_REGEX, ParameterParsingMixin.PARAM_REGEX)
        self.known_keys = keys


class MechanicsBlockParser(Parser):
    """Base class for mechanics block parsers.

    Block parsers own a subtree in the output and typically span multiple
    lines. They create a root element in `begin`, may add additional content as
    nodes are parsed, and can perform finalization in `finalize`.
    """

    def __init__(self, names: NameCollection, line_regex: str, param_regex: str | None = None) -> None:
        """Initialize the block parser.

        Args:
            names: Name collection for the block.
            line_regex: Regular expression string for the opening line.
            param_regex: Optional regex for parsing individual key=value parameters.
        """
        super().__init__(names, line_regex, param_regex)

    def begin(self, ctx: Context, data: str) -> None:
        """Create the block's root element and push it to the Context stack.

        Matches the block's opening line with the parser's `line_regex` and
        builds an argument dictionary from its match groups.

        If the opening line cannot be matched, a generic block element is
        created containing a textual representation of the original input.

        Note that the block's root element created here is only a temporary
        dummy `<div>`. Template rendering and creating the block's proper
        element happen in the `finalize()` call.

        Args:
            ctx: Current parsing `Context`.
            data: Block parameter string from the opening line.
        """
        matches = self._match(data)
        if matches is None:
            logger.warning(f"Failed to match {self.names.name}: '{data}'")
            args = {"block_name": self.names.name, "content": data}
        else:
            args = self.handle_args(matches, ctx)

        # Don't bother with templates yet, finalize() will handle that,
        # we just need a container at this point
        element = etree.SubElement(ctx.parent, "div")

        block = BlockContext(self.names, element, matches, args)
        ctx.push(block)

    def finalize(self, ctx: Context) -> None:
        """Finalize the block after all nested nodes have been parsed.

        If the parser matched its `line_regex` in `begin()`, the block's
        template is looked up from the active `Templater`, otherwise the
        default block fallback template is used.

        If the template lookup returns `None`, nothing is rendered,
        and the block remains in its initial, dummy `<div>`. Otherwise,
        renders the template with its parsed arguments (found in `ctx.args`)
        and replaces the block's temporary `<div>` container parent with it.

        Calls two finalization methods that subclasses may override:
         - `finalize_nodes()` to add extra nodes into the block
         - `finalize_args()` to tweak template parameters before rendering

        Args:
            ctx: Current parsing `Context`.
        """
        self.finalize_nodes(ctx)

        if ctx.matches is not None:
            template = get_templater().get_template(self.names.template, "blocks")
        else:
            logger.debug(f"Using fallback template for {self.names.name} block")
            template = get_templater().get_default_template("blocks")

        if template is None:
            # Do nothing, the block is already in a dummy <div>,
            # keep it as is and use that as fallback.
            pass
        else:
            args = self.finalize_args(ctx)
            new_root = etree.fromstring(template.render(args))
            ctx.replace_root(new_root)

        ctx.pop()

    def finalize_nodes(self, ctx: Context) -> None:
        """Add extra nodes to the block during finalization.

        Called at the beginning of the finalization step, before the template
        lookup and possible root node replacement.

        Subclasses can override this method to add extra nodes, such as
        a roll result summary in the move block. Does nothing by default.

        Args:
            ctx: Current parsing `Context`.
        """
        pass

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


class ParameterBlockParser(ParameterParsingMixin, MechanicsBlockParser):
    """Block parser that uses the generic key=value parameter mechanism.

    Automatically parses parameters in the format:
        `key1=value1 key2="value2" ...`
    Separates known from unknown parameters and provides a dict containing
    the parsed known parameters along an `extra` entry with a dict of the
    unknown parameters to the `handle_args()` method.

    Known keys must be provided in the constructor.

    Note that defining a key as known only defined that it _can_ be expected
    in the parsed line, not that it _must_ be there. If a known key isn't
    found, it's simply omitted from the collected args dict.

    Attributes:
        known_keys: List of expected parameter names.
    """
    known_keys: list[str]

    def __init__(self, names: NameCollection, keys: list[str]) -> None:
        """Initialize with expected parameter keys.

        Args:
            names: Name collection for the block.
            keys: List of known/expected parameter names.
        """
        super().__init__(names, ParameterParsingMixin.PARAMS_REGEX, ParameterParsingMixin.PARAM_REGEX)
        self.known_keys = keys

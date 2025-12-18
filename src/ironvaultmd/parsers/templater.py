"""Jinja templating helper for mechanics rendering.

This module provides a thin wrapper around Jinja to load default HTML
templates shipped with the package and to optionally override them with
user-provided snippets at runtime. Parsers obtain templates via the shared
`templater` instance defined at the bottom of this module.
"""

import logging
from dataclasses import dataclass

from jinja2 import Template, PackageLoader, Environment, TemplateNotFound

from ironvaultmd import logger_name

logger = logging.getLogger(logger_name)

@dataclass
class UserTemplates:
    """Container for optional user-provided template overrides.

    Set any field to a non-empty string to override the corresponding default
    template. Set to an empty string to disable rendering for that element, or
    to `None` to use the packaged default template.

    Attributes:
        actor_block: Template for the `actor` block.
        mechanics_block: Template for the main iron-vault-mechanics content block.
        move_block: Template for the `move` block.
        oracle_block: Template for the `oracle` block.
        add: Template for the `add` node.
        burn: Template for the `burn` node.
        clock: Template for the `clock` node.
        impact: Template for the `impact` node.
        initiative: Template for the `initiative` node.
        meter: Template for the `meter` node.
        move: Template for the `move` node.
        ooc: Template for the out-of-character node.
        oracle: Template for the `oracle` node.
        position: Template for the `position` node.
        progress: Template for the `progress` node.
        progress_roll: Template for the `progress-roll` node.
        reroll: Template for the `reroll` node.
        roll: Template for the `roll` node.
        track: Template for the `track` node.
        xp: Template for the `xp` node.
        link: Template for wiki links rendered by the links processor.
    """
    # Blocks
    actor_block: str | None = None
    mechanics_block: str | None = None
    move_block: str | None = None
    oracle_block: str | None = None
    # Nodes
    add: str | None = None
    burn: str | None = None
    clock: str | None = None
    impact: str | None = None
    initiative: str | None = None
    meter: str | None = None
    move: str | None = None
    ooc: str | None = None
    oracle: str | None = None
    position: str | None = None
    progress: str | None = None
    progress_roll: str | None = None
    reroll: str | None = None
    roll: str | None = None
    track: str | None = None
    xp: str | None = None
    # Other elements
    link: str | None = None


class Templater:
    """Helper that resolves Jinja templates for mechanics elements.

    It first checks for an override provided via `UserTemplates` and, if not
    present, falls back to loading the default template file from the
    `templates` package directory.

    Attributes:
        block_fallback_template: Fallback template string for block elements
            that don't have a template defined.
    """

    block_fallback_template: str = "<div></div>"

    def __init__(self):
        """Initialize the templating environment."""
        self.template_loader = PackageLoader('ironvaultmd.parsers', 'templates')
        self.template_env = Environment(loader=self.template_loader, autoescape=True)
        self.user_templates = UserTemplates()

    def load_user_templates(self, user_templates: UserTemplates):
        """Load or reset user template overrides.

        Args:
            user_templates: A `UserTemplates` instance whose non-`None` values
                will override the corresponding defaults. `None` resets an
                override to packaged defaults, an empty string disables output
                for that template.
        """
        for name, value in user_templates.__dict__.items():
            if value is not None:
                logger.debug(f"Setting user template for '{name}': '{value}'")
                self.user_templates.__dict__[name] = value
            else:
                # In case there are multiple calls to this method, ensure that
                # potentially previously set user templates are reset to None
                self.user_templates.__dict__[name] = None


    def get_template(self, name: str, template_type: str = "") -> Template | None:
        """Return a Jinja template for a node or block `name`, or `None`.

        Looks up the `name` and `block_type` to a matching key in the
        `UserTemplates` and creates a `Template` from it. If none is set,
        looks up a matching file in the templates/ directory and creates
        a `Template` from it.

        In case the user-defined template override is an empty string,
        or the template file doesn't exist, the return value depends on
        the `template_type`.:
         - For "nodes" and default "" types, `None` is returned, and
           that specific template will not be rendered at all.
         - For "blocks" types, a fallback `Template` created from
           `block_fallback_template` is returned as block elements
           always need a container.

        Args:
            name: Element name, e.g., `Progress Roll` or `oracle`.
            template_type: "blocks", "nodes", or default "".

        Returns:
            A compiled Jinja `Template` or `None` when explicitly disabled.
        """
        logger.debug(f"Getting {template_type} template for '{name}'")
        key = name.lower().replace(' ', '_')

        user_template = self._lookup_user_template(key, template_type)

        if isinstance(user_template, str):
            # User override template string found
            if str(user_template) == '':
                logger.debug("  -> found empty user template")

                if template_type == "blocks":
                    # Block template with empty-string user override.
                    # Blocks need a container, though, so return fallback.
                    return Template(self.block_fallback_template)

                # For other types, return None to disable rendering it
                return None

            # Return a Template from the non-empty user override string
            logger.debug("  -> found user template")
            return Template(user_template)

        file_template = self._lookup_file_template(key, template_type)

        if file_template is not None:
            logger.debug("  -> using file template")
            return file_template

        logger.debug("  -> no template found")

        if template_type == "blocks":
            # Again, blocks need a container, return fallback
            return Template(self.block_fallback_template)

        return None

    def _lookup_user_template(self, key: str, template_type: str) -> str | None:
        """Look up a user template for the given `key` and `template_type`.

        If it's found from the `UserTemplates`, its value is returned.
        If it isn't found, or its value is set to `None`, `None` is returned.

        Args:
            key: Template name normalized as the `UserTemplates` key.
            template_type: Template type, "blocks", "nodes", or "".

        Returns:
            Template string if found and set, `None` otherwise.
        """
        if template_type == "blocks":
            key += "_block"
        return self.user_templates.__dict__.get(key, None)

    def _lookup_file_template(self, key: str, template_type: str) -> Template | None:
        """Look up a template file for the given `key` and `template_type`.

        If a matching file is found, its compiled `Template` is returned.
        If no file is found, loading it fails, or `template_type` is neither
            `blocks`, `nodes`, or an empty string, `None` is returned

        Args:
            key: Template name normalized as the filename key.
            template_type: Template type, "blocks", "nodes", or "".

        Returns:
            Compiled `Template` if found, `None` otherwise.
        """
        if template_type not in ["nodes", "blocks", ""]:
            return None

        dir_path = "" if template_type == "" else f"{template_type}/"
        filename = f"{dir_path}{key}.html"

        template: Template | None = None
        try:
            template = self.template_env.get_template(filename)
        except TemplateNotFound:
            logger.warning(f"Failed to look up template for {key}")

        return template


templater = Templater()
"""Shared templater instance used by parsers to render output."""
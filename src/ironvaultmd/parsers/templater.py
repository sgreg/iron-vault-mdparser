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
    """

    def __init__(self) -> None:
        """Initialize the templating environment."""
        self.template_loader = PackageLoader('ironvaultmd.parsers', 'templates')
        self.template_env = Environment(loader=self.template_loader, autoescape=True)
        self.user_templates = UserTemplates()

    def load_user_templates(self, user_templates: UserTemplates) -> None:
        """Load or reset user template overrides.

        Args:
            user_templates: A `UserTemplates` instance whose non-`None` values
                will override the corresponding defaults. `None` resets an
                override to packaged defaults, an empty string disables output
                for that template.
        """
        for name, value in vars(user_templates).items():
            if value is not None:
                logger.debug(f"Setting user template for '{name}': '{value}'")
                setattr(self.user_templates, name, value)
            else:
                # In case there are multiple calls to this method, ensure that
                # potentially previously set user templates are reset to None
                setattr(self.user_templates, name, None)


    def get_template(self, name: str, template_type: str = "") -> Template | None:
        """Return a Jinja template for a node or block `name`, or `None`.

        Looks up the `name` and `block_type` to a matching key in the
        `UserTemplates` and creates a `Template` from it. If none is set,
        looks up a matching file in the templates/ directory and creates
        a `Template` from it. If that doesn't exist or can't be read,
        `None` is returned.

        Args:
            name: Element name, e.g., `Progress Roll` or `oracle`.
            template_type: "blocks", "nodes", or default "".

        Returns:
            A compiled Jinja `Template` or `None` when explicitly disabled
                or reading the template file fails or doesn't exist.
        """
        logger.debug(f"Getting {template_type} template for '{name}'")
        key = name.lower().replace(' ', '_')

        user_template = self._lookup_user_template(key, template_type)

        if isinstance(user_template, str):
            # User override template string found
            if str(user_template) == '':
                # Empty string, template is explicitly disabled
                logger.debug("  -> found empty user template")
                return None

            # Return a Template from the non-empty user override string
            logger.debug("  -> found user template")
            return Template(user_template)

        file_template = self._lookup_file_template(key, template_type)

        if file_template is not None:
            logger.debug("  -> using file template")
            return file_template

        logger.debug("  -> no template found")
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
        return getattr(self.user_templates, key, None)

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

        dir_prefix = f"{template_type}/" if template_type else ""
        filename = f"{dir_prefix}{key}.html"

        template: Template | None = None
        try:
            template = self.template_env.get_template(filename)
        except TemplateNotFound:
            logger.warning(f"Failed to look up template for {key}")

        return template


templater = Templater()
"""Shared templater instance used by parsers to render output."""
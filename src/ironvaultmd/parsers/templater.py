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
        """Return a Jinja template by element name or `None`.

        The `name` is normalized to match a template file named
        `<name>.html` where `name` is lowercased and spaces replaced with
        underscores. User overrides take precedence.

        Args:
            name: Element name, e.g., `Progress Roll` or `oracle`.
            template_type: "block", "node", or default ""

        Returns:
            A compiled Jinja `Template` or `None` when explicitly disabled.

        Raises:
            TemplateNotFound: If no default template exists for `name` and no
                override is provided.
        """
        logger.debug(f"Getting template for '{name}'")
        key = name.lower().replace(' ', '_')

        user_template = self.user_templates.__dict__.get(key, None)
        if isinstance(user_template, str):
            if str(user_template) == '':
                logger.debug("  -> found empty user template")
                return None

            logger.debug("  -> found user template")
            return Template(user_template)

        if template_type in ["nodes", "blocks"]:
            filename = f"{template_type}/{key}.html"
        else:
            filename = f"{key}.html"

        try:
            logger.debug("  -> using default template")
            return self.template_env.get_template(filename)
        except TemplateNotFound as err:
            logger.warning(f"Template {filename} not found") # TODO just make this return None?
            raise err

templater = Templater()
"""Shared templater instance used by parsers to render output."""
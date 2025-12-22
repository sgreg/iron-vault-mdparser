"""Jinja templating for mechanics rendering.

This module provides context-aware template management for Iron Vault mechanics
rendering. It wraps Jinja2 to load HTML templates from either package-provided
defaults or custom directories, with optional user-defined overrides.

The main components are:

- `UserTemplates`: A dataclass holding optional template string overrides for
  blocks, nodes, and other mechanics elements.
- `Templater`: The core template loader and renderer that checks user overrides
  first, then falls back to file-based templates.
- Context-local templater management via `get_templater()`, `set_templater()`,
  `reset_templater()`, and `clear_templater()` for multi-instance support.

Typical usage through the `IronVaultExtension`:

```python
from ironvaultmd.ironvault import IronVaultExtension
from ironvaultmd.parsers.templater import UserTemplates

user_templates = UserTemplates(
    roll='<div class="custom-roll">{{ action }}+{{ stat }}</div>'
)

md = Markdown(extensions=[IronVaultExtension(templates=user_templates)])
html = md.convert(your_markdown_text)
```
"""

import logging
from contextvars import ContextVar
from dataclasses import dataclass

from jinja2 import Template, PackageLoader, Environment, TemplateNotFound, FileSystemLoader

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
    """Resolves Jinja templates for mechanics elements.

    Provides a two-tier template lookup: first checks for a user-provided
    template override in `UserTemplates`, then falls back to loading a
    template file from either a user-provided directory or the package's
    default `templates` folder.

    Caches compiled templates for performance and maintains a set of
    default fallback templates for nodes, blocks, and mechanics containers.

    Attributes:
        template_loader: Jinja2 loader (`FileSystemLoader` for user-provided,
            directory, `PackageLoader` for package defaults).
        template_env: Jinja2 `Environment` instance for template rendering.
        user_templates: `UserTemplates` instance holding optional overrides.
        theme: Optional path to a user-provided templates directory.
        default_templates: Dictionary of fallback `Template` instances for
            nodes, blocks, and mechanics.
        templates_cache: Cache of compiled templates keyed by
            `"{template_type}:{name}"`.
    """

    template_loader: FileSystemLoader | PackageLoader | None = None
    template_env: Environment | None = None
    user_templates: UserTemplates | None = None
    theme: str | None = None
    default_templates: dict[str, Template]
    templates_cache: dict[str, Template]

    def __init__(self, theme: str | None = None, user_templates: UserTemplates | None = None) -> None:
        """Initialize the templating environment.

        Sets up Jinja template handling with either a user-provided directory
        or package-provided templates as the source. User templates can be
        provided to override defaults.

        Args:
            theme: Optional path to a directory containing custom templates.
            user_templates: Optional `UserTemplates` instance containing
                template overrides.
        """
        if theme:
            logger.debug(f"Using theme templates {theme}")
            self.template_loader = FileSystemLoader(theme)
        else:
            logger.debug("Using package-provided templates")
            self.template_loader = PackageLoader('ironvaultmd.parsers', 'templates')

        self.user_templates = UserTemplates()

        if user_templates and isinstance(user_templates, UserTemplates):
            logger.debug(f"Setting user templates: {user_templates}")
            self.load_user_templates(user_templates)
        elif user_templates:
            logger.error("Provided template config is not a UserTemplates instance")

        self.template_env = Environment(loader=self.template_loader, autoescape=True)
        self.templates_cache = {}
        self._set_default_templates()

    def load_user_templates(self, user_templates: UserTemplates | None) -> None:
        """Load user template overrides.

        Args:
            user_templates: A `UserTemplates` instance whose non-`None` values
                will override the corresponding defaults. `None` resets an
                override to packaged defaults, an empty string disables output
                for that template.
        """
        if not user_templates:
            logger.warning("Trying to load user templates, but no user templates are set")
            return

        for name, value in vars(user_templates).items():
            if value is not None:
                logger.debug(f"Setting user template for '{name}': '{value}'")
                setattr(self.user_templates, name, value)
            else:
                # In case there are multiple calls to this method, ensure that
                # potentially previously set user templates are reset to None
                setattr(self.user_templates, name, None)

    def _set_default_templates(self) -> None:
        """Initialize the default fallback templates.

        Creates a minimal `<div></div>` fallback and attempts to load
        default templates for nodes, blocks, and mechanics. If loading
        fails (e.g., user-provided directory doesn't contain the matching
        template file), the minimal fallback is used or those as well.
        """
        default = Template("<div></div>")
        self.default_templates = {
            "default": default,
            "nodes": self.get_template("node", "nodes") or default,
            "blocks": self.get_template("block", "blocks") or default,
            "mechanics": self.get_template("mechanics", "blocks") or default,
        }

    def get_default_template(self, key: str) -> Template:
        """Retrieve a default fallback template by key.

        Args:
            key: Template key (`"nodes"`, `"blocks"`, `"mechanics"`)

        Returns:
            The corresponding default `Template`, or the generic `<div></div>`
            fallback if the key is not recognized.
            """
        if key in self.default_templates:
            return self.default_templates[key]
        return self.default_templates["default"]

    def get_template(self, name: str, template_type: str = "") -> Template | None:
        """Get a compiled template for a mechanics element.

        Checks the cache first, then delegates to `_get_template()` if
        not found. The result is cached for future lookups.

        Args:
            name: Element name, e.g., `"Progress Roll"`, or `"oracle"`.
            template_type: `"blocks"`, `"nodes"`, or `""` for other elements.

        Returns:
            A compiled Jinja `Template` or `None` when explicitly disabled
            or reading the template file fails / it doesn't exist.
        """
        cache_key = f"{template_type}:{name}"
        if cache_key not in self.templates_cache:
            self.templates_cache[cache_key] = self._get_template(name,template_type)
        return self.templates_cache[cache_key]

    def _get_template(self, name: str, template_type: str = "") -> Template | None:
        """Return a Jinja template for a node or block `name`, or `None`.

        First checks for a user-provided template override in `UserTemplates`.
        If not found or set to `None`, attempts to load the corresponding
        template file from the configured template directory - either the
        one provided by the user, or the package-provided default.

        If the user-provided template override is an empty string, or file
        lookup is unsuccessful, `None` is returned to disable rendering
        of that specific template.

        Args:
            name: Element name, e.g., `Progress Roll` or `oracle`.
            template_type: "blocks", "nodes", or default "".

        Returns:
            A compiled Jinja `Template` or `None` when explicitly disabled
            or reading the template file fails / it doesn't exist.
        """
        logger.info(f"[ctx {hex(id(self))}] Getting {template_type} template for '{name}'")
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


_templater_var: ContextVar[Templater | None] = ContextVar('templater', default=None)
"""Context variable for managing per-context `Templater` instances."""

def get_templater() -> Templater:
    """Get the current context's `Templater` instance.

    Returns the context-local `Templater` if one exists, otherwise
    returns a default instance (mainly for testing and simple use cases).

    Returns:
        The context-specific `Templater` instance.
    """
    templater_instance = _templater_var.get()

    if templater_instance is None:
        # Fallback to a default instance if no context is set
        logger.warning("TEMPLATER: No instance set, creating default fallback")
        templater_instance = Templater()
        _templater_var.set(templater_instance)

    logger.debug(f"TEMPLATER: get instance {hex(id(templater_instance))}")
    return templater_instance

def set_templater(templater_instance: Templater) -> None:
    """Set a `Templater` instance for the current context.

    Args:
        templater_instance: The `Templater` to use in this context.
    """
    logger.debug(f"TEMPLATER: set instance {hex(id(templater_instance))}")
    _templater_var.set(templater_instance)

def reset_templater() -> None:
    """Reset the current context's templater to a fresh instance.

    Creates a new default `Templater` instance and sets it as the current
    context's templater. Mainly used for testing to ensure a clean state.
    """
    _templater_var.set(Templater())
    logger.debug(f"TEMPLATER: rst instance {_templater_var.get()}")

def clear_templater() -> None:
    """Unset the current context's templater.

    Sets the context's templater to `None`, which will trigger creation
    of a default fallback instance on the next call to `get_templater()`.
    Mainly used for testing to verify default fallback behavior.
    """
    _templater_var.set(None)
    logger.debug("TEMPLATER: clr instance")

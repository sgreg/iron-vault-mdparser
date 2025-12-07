import logging
from dataclasses import dataclass

from jinja2 import Template, PackageLoader, Environment, TemplateNotFound

logger = logging.getLogger("ironvaultmd")

@dataclass
class UserTemplates:
    # Nodes
    add: str | None = None
    burn: str | None = None
    clock: str | None = None
    impact: str | None = None
    initiative: str | None = None
    meter: str | None = None
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
    roll_result: str | None = None


class Templater:
    def __init__(self):
        self.template_loader = PackageLoader('ironvaultmd.parsers', 'templates')
        self.template_env = Environment(loader=self.template_loader, autoescape=True)
        self.user_templates = UserTemplates()

    def load_user_templates(self, user_templates: UserTemplates):
        for name, value in user_templates.__dict__.items():
            if value is not None:
                logger.debug(f"Setting user template for '{name}': '{value}'")
                self.user_templates.__dict__[name] = value
            else:
                # In case there are multiple calls to this method, ensure that
                # potentially previously set user templates are reset to None
                self.user_templates.__dict__[name] = None


    def get_template(self, name: str) -> Template:
        logger.debug(f"Getting template for '{name}'")
        key = name.lower().replace(' ', '_')

        user_template = self.user_templates.__dict__.get(key, None)
        if isinstance(user_template, str):
            logger.debug("  -> found user template")
            return Template(user_template)

        filename = f"{key}.html"

        try:
            logger.debug("  -> using default template")
            return self.template_env.get_template(filename)
        except TemplateNotFound as err:
            logger.warning(f"Template {filename} not found")
            raise err

templater = Templater()
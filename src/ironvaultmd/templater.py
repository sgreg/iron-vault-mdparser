import logging
import traceback

from jinja2 import TemplateNotFound, PackageLoader, Environment, Template

logger = logging.getLogger("ironvaultmd")

class Templater:
    def __init__(self):
        self.template_loader = PackageLoader('ironvaultmd.parsers', 'templates')
        self.template_env = Environment(loader=self.template_loader, autoescape=True)

    def get(self, name: str, strict: bool = False) -> Template | None:
        if not name.endswith(".html"):
            filename = f"{name.lower().replace(' ', '-')}.html"
        else:
            filename = name

        try:
            return self.template_env.get_template(filename)
        except TemplateNotFound as err:
            logger.warning(f"Template {filename} not found")
            logger.debug(''.join(traceback.TracebackException.from_exception(err).format()))
            if strict:
                raise err
            return None

templater = Templater()

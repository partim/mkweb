
class Config(object):
    def initialize(self, source_base, target_base, template_path=None):
        import os.path
        import jinja2

        self.source_base = source_base
        if template_path is None:
            template_path = os.path.join(source_base, "templates")
        self.jinja_environment = jinja2.Environment(
                                loader=jinja2.FileSystemLoader(template_path))
        self.target_base = target_base


config = Config()

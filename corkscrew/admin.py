""" corkscrew.admin
"""
from corkscrew.views.base import View
from corkscrew.blueprint import BluePrint

from pygments import highlight
from pygments.lexers import IniLexer
from pygments.formatters import HtmlFormatter

class AdminView(View):
    url           = '/_admin'
    template      = 'admin.html'
    requires_auth = True
    blueprint     = BluePrint(__name__,
                              template_folder='templates')

    def get_ctx(self, **kargs):
        result = super(AdminView,self).get_ctx(**kargs)
        shell_ns = self.settings.shell_namespace()
        result.update(shell_ns)
        items = [] if not self['schema'] else \
                shell_ns[self['schema']].objects.all()
        with open(self.settings.settings_file, 'r') as fhandle:
            result.update(
                items=items,
                config_css=HtmlFormatter().get_style_defs('.highlight'),
                config= highlight(fhandle.read(),
                                  IniLexer(),
                                  HtmlFormatter()))
        return result

    def main(self):
        return self.render_template(env='?')

class SettingsView(View):
    url           = '/__settings__'
    requires_auth = True
    template      = "admin_settings.html"

    def main(self):
        return self.render(
                app_data=self._get_app_data(),
                views=self.settings._installed_views)

    def _get_app_data(self):
        data = dict()
        for x in dir(self.app):
            if not x.startswith('_'):
                val = getattr(self.app,x)
                if not callable(val):
                    tmp = str(val).replace('<','(').replace('>',')')
                    data[x]=tmp
        uninteresting = [
            'debug_log_format',
            'permanent_session_lifetime',
            ]
        for x in uninteresting:
            data.pop(x, None)
        data=data.items()
        data.sort()
        return data

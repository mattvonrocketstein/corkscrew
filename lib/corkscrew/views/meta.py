"""
"""
from .base import View

class SettingsView(View):
    url = '/__settings__'
    requires_auth = True

    @View.use_local_template
    def main(self):
        """
        <style>
          table {
            border: 1px solid grey;
            width:90%;
            margin-bottom:40px;
            margin-left:15px;
           }
          h3 { margin-left:7px;margin-bottom:5px; }
        </style>
        <h3><b>Corkscrew views</b></h3>
        <table>
          <tr><td>view</td><td>url</td><td>from module</td></tr>
          <tr><td colspan=4><hr/></td></tr>
          {% for v in views %}
          <tr>
            <td><b>{{v.__name__}}</b></td>
            <td><i>{{v.url}}</i></td>
            <td><small>{{v.__class__.__module__}}<small></td>
          </tr>
          {%endfor%}
        </table>

        <h3><b>Flask app info</b></h3>
        <table>
          <tr><td>setting name</td><td>value in app</td></tr>
          <tr><td colspan=2><hr/></td></tr>
          {%for x,y in app_data%}
          <tr>
            <td valign=top>{{x}}</td><td>{{y}}</td>
          </tr>{%endfor%}
        </table>
        """
        return dict(
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

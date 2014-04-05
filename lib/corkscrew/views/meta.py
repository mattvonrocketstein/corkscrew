"""
"""
from .base import View

class SettingsView(View):
    url = '/__settings__'
    requires_auth = True

    @View.use_local_template
    def main(self):
        """
        <table>
          <tr>
            <td><b>root</b></td><td>{{rootpath}}</td>
          </tr>
        </table>
        """
        return dict(rootpath=self.app.root_path)

class ListViews(View):
    url = '/__views__'
    requires_auth = True

    @View.use_local_template
    def main(self):
        """
        {# renders a list of all views.. #}
        <table>
          <tr>
             <td>view</td>
             <td>url</td>
             <td>from module</td>

          </tr>
          <tr><td colspan=4> <hr/></td></tr>
          {% for v in views %}
          <tr>
            <td><b>{{v.__name__}}</b></td>
            <td><i>{{v.url}}</i></td>
            <td><small>{{v.__class__.__module__}}<small></td>
          </tr>
          {%endfor%}
        </table>
        """
        # TODO: might as well organize 'views' by schema
        return dict(views=self.settings._installed_views)

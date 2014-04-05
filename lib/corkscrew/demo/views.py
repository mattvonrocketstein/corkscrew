""" corkscrew.demo.views
"""

from collections import OrderedDict

from corkscrew.views import View
from corkscrew.comet import SijaxDemo
from corkscrew.views.meta import ListViews, SettingsView

class Home(View):
    url = '/'

    @View.use_local_template
    def main(self):
        """
        <strong>various demos</strong>
        <table style="margin-left:15px">
            {% for k,v in demos.items()%}
            <tr>
            <td><b><a href="{{k}}">{{k}}</a></b></td>
            <td>{{v}}</td>
            </tr>
            {%endfor%}
        </table><hr>
        <strong>app metatdata</strong>
        <table style="margin-left:15px">
            {% for k,v in app_metadata.items()%}
            <tr><td><b>{{k}}</b></td><td>{{v}}</td></tr>
            {%endfor%}
        </table><hr>
        """
        return dict(
            demos=OrderedDict(
                [ ['/comet','comet demo (via sijax)'],
                  ['/json_editor','json editor'],
                  ['/__views__' , 'views in this runtime'],
                  ['/__settings__' , 'settings in this runtime'],
                  ]),
            app_metadata=dict(
                static_folder=self.app.static_folder,
                jinja_env_globals=self.app.jinja_env.globals.keys(),
                rootpath=self.app.root_path))



from corkscrew.views import JSONEdit
import demjson
class DemoJSONEdit(JSONEdit):
    def get_json(self):
        return demjson.encode(
            dict(string= "foo",
                 number= 5,
                 array= [1, 2, 3],
                 object= dict(
                     property="value",
                     subobj = dict(
                         arr=["foo", "ha"],
                         numero= 1))))

__views__ = [
    Home,
    DemoJSONEdit,
    SijaxDemo,
    type('DemoListView', (ListViews,), dict(requires_auth=False)),
    type('DemoSettingsView', (SettingsView,), dict(requires_auth=False)),
    ]

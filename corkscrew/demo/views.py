""" corkscrew.demo.views
"""
import demjson
from collections import OrderedDict

from corkscrew.admin import AdminView
from corkscrew.views import View
from corkscrew.views import JSONEdit
from corkscrew.comet import SijaxDemo
from corkscrew.admin import SettingsView
from corkscrew.views.nav import Nav, MakeMenu
from corkscrew.proxy import RedirectsFromSettings#, ProxyFromSettings

class MyMenu(MakeMenu):
    pass

class Home(View):

    url      = '/'
    template = 'demo_home.html'

    def main(self):
        return self.render(
            demos=OrderedDict(
                [ ['/comet?start=1','comet demo (via sijax)'],
                  ['/json_editor','a simple json editor'],
                  ['/redirect', ('example redirect (define as '
                                 'many as you want in the .ini)')],
                  ['/_admin' , 'shows admin tools (schema, views, config, etc)'],
                  ["/_make_menu?menu=[['menu-header',[['menu-item','/']]]]" ,
                   'a parametric menu-maker, suitable for loading with ajax'],
                  ['/__settings__' , 'settings in this runtime'],
                  ]),
            app_metadata=dict(
                static_folder=self.app.static_folder,
                jinja_env_globals=self.app.jinja_env.globals.keys(),
                rootpath=self.app.root_path))


class DemoPage(View):
    url = '/demo_page'
    @View.use_local_template
    def main(self):
        """
        simple demo page.<br/><br/><hr/>
        this template is embedded in the view code<br/>
        for simplicity, but of course you can have
        external templates as well.
        """
        return dict()


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
    Home, Nav,
    DemoPage,
    DemoJSONEdit,
    SijaxDemo,
    RedirectsFromSettings,
    MakeMenu,
    type('DemoAdminView', (AdminView,), dict(requires_auth=False)),
    type('DemoSettingsView', (SettingsView,), dict(requires_auth=False)),
    ]

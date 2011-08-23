""" corkscrew.settings
"""

import os
import ConfigParser

from flask import Flask
from jinja2 import FileSystemLoader
from werkzeug import check_password_hash, generate_password_hash

from report import report as report
from .reflect import namedAny

class FlaskSettings(object):
    """ combination option parser / settings parser for flask
        that reads the .ini format.
    """

    DEFAULT_SETTINGS = None

    @classmethod
    def get_parser(kls):
        from optparse import OptionParser
        parser = OptionParser()
        parser.set_conflict_handler("resolve")
        parser.add_option("--port",  dest="port",
                          default='', help="server listen port")
        parser.add_option("--shell", dest="shell",
                          default=False, help="application shell",
                          action='store_true')
        parser.add_option("--config", dest='config',
                          default="",
                          help="use config file")
        parser.add_option("--encode", dest='encode',
                          default="",
                          help="encode password hash using werkzeug")
        return parser

    def __mod__(self, other):
        return dict([ [x[len(other)+1:], self[x]] for x in self._settings.keys() if x.startswith(other+'.')])

    def __contains__(self,other):
        """ dictionary compatability """
        return other in self._settings

    def __getitem__(self,k):
        """ dictionary compatability """
        return self._settings[k]


    def __init__(self):
        """
            first load the default config so that overrides don't need
            to mention everything.  update default with the config
            specified by the command line optionparser, then
            update that with any other overrides delivered to the parser.
        """
        self.options, self.args = self.get_parser().parse_args()
        if self.DEFAULT_SETTINGS:
            self._settings = self.load(file=self.DEFAULT_SETTINGS)
        else:
            self._settings = {}
        self._settings.update(self.load(file=self.options.config))

        # a few command line options are allowed to override the .ini
        if self.options.port:
            self._settings.update({'flask.port':self.options.port})

        # build a special section for things the user wants,
        # ie, things that have been passed into the option
        # parser but are not useful in the .ini
        self._settings.update({'user.shell' : self.options.shell and 'true' or ''})
        self._settings.update({'user.encode_password':self.options.encode})

        # TODO: move this to ConfigParser subclass.
        # allow pythonic comments in the .ini files,
        # and strip any trailing whitespace.
        for k,v in self._settings.items():
            self._settings[k]=v.strip()
            if '#' in v:
                self._settings[k]=v[:v.find('#')]
        report('finished parsing settings from',
               Global=self.DEFAULT_SETTINGS,
               Local=self.options.config)
        global settings
        settings=self

    @property
    def app(self):
        """ derive flask app based on the combination of command-line
            options and the contents of the .ini files
        """

        ## set flask specific things that are non-optional
        app_name = self['flask.app']
        secret_key = self['flask.secret_key']
        app = Flask(app_name)
        app.secret_key = secret_key

        ## set flask specific things that are optional
        if 'flask.template_path' in self:
            app.jinja_loader = FileSystemLoader(self['template_path'])
        if 'flask.before_request' in self:
            before_request = self['flask.before_request']
            before_request = namedAny(before_request)
            app.before_request(before_request)
        if 'flask.after_request' in self:
            after_request = self['flask.after_request']
            after_request = namedAny(after_request)
            app.after_request(after_request)

        ## setup views
        view_holder = self['corkscrew.views']
        view_list = namedAny(view_holder)
        [ v(app=app,settings=self) for v in view_list]

        @app.route("/favicon.ico")
        def favicon():
            return app.send_static_file("favicon.ico")

        return app

    def load(self, file, config={}):
        """ returns a dictionary with key's of the form
            <section>.<option> and the values
        """
        if not file: return {}
        if not os.path.exists(file):
            raise ValueError, 'config file @{f} does not exist'.format(f=file)
        config = config.copy()
        cp = ConfigParser.ConfigParser()
        cp.read(file)
        for sec in cp.sections():
            name = sec.lower()
            for opt in cp.options(sec):
                config[name + "." + opt.lower()] = cp.get(sec, opt).strip()
        return config

    def run(self, *args, **kargs):
        """ """
        if self['user.shell']:
            from IPython import Shell; Shell.IPShellEmbed(argv=['-noconfirm_exit'])()
        elif self['user.encode_password']:
            print generate_password_hash(self['user.encode_password'])
        else:
            app = self.app
            app.run(host=self['flask.host'],
                    port=int(self['flask.port']),
                    debug=self['flask.debug'])
Settings=FlaskSettings

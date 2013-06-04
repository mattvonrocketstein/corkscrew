""" corkscrew.settings
"""

import os
import warnings
import platform
import importlib
import configparser

from flask import Flask, url_for
from jinja2 import FileSystemLoader
from werkzeug import check_password_hash, generate_password_hash

import report as reporting
from corkscrew.reflect import namedAny

report = reporting.getReporter(label=False)

class SettingsError(Exception):
    pass

class FlaskSettings(object):
    """ combination option parser / settings parser for flask
        that reads the .ini format.
    """

    default_file = 'corkscrew.ini'

    @classmethod
    def get_parser(kls):
        """ build the default parser """
        from optparse import OptionParser
        parser = OptionParser()
        parser.set_conflict_handler("resolve")
        parser.add_option("--port",  dest="port",
                          default='', help="server listen port")
        parser.add_option("--runner",  dest="runner",
                          default='', help="dotpath for app server")
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
        """ namespacing:
            get all the settings that start with a certain string
        """
        return dict([ [x[len(other)+1:], self[x]] \
                      for x in self._settings.keys() \
                      if x.startswith(other+'.')])

    def __contains__(self, other):
        """ dictionary compatability """
        return other in self._settings

    def __getitem__(self,k):
        """ dictionary compatability """
        return self._settings[k]

    @property
    def settings_file(self):
        if self.options.config:
            _file = self.options.config
        else:
            _file = self._init_filename or \
                    os.environ.get('CORKSCREW_SETTINGS') or \
                    self.default_file
        _file = os.path.expanduser(_file)
        return _file

    def __init__(self, filename=None):
        """
            first load the default config so that overrides don't need
            to mention everything.  update default with the config
            specified by the command line optionparser, then
            update that with any other overrides delivered to the parser.
        """
        self._app_cache = None
        self._init_filename = filename
        self.options, self.args = self.get_parser().parse_args()

        # special case
        self.done=False
        if self.options.encode:
            print generate_password_hash(self.options.encode)
            self.doit()
            self.done=True
            return

        #self._settings = {}
        #self._settings.update(self.load(file=self.settings_file))
        #self._settings.update(self._config_parser)
        self._settings = self.load(file=self.settings_file)

        # a few command line options are allowed to override the .ini
        if self.options.port:
            self._settings.update({'flask.port':self.options.port})

        # build a special section for things the user wants,
        # ie, things that have been passed into the option
        # parser but are not useful in the .ini
        if 'user' not in self._settings:
            self._settings['user']={}
        self._settings['user']['shell'] = self.options.shell and 'true' or ''
        self._settings['user']['encode_password'] = self.options.encode
        self._settings['user']['runner'] = self.options.runner

        def prepare(k, v):
            """ allow pythonic comments in the .ini files,
                and strip any trailing whitespace.

                TODO: move this to ConfigParser subclass.
            """
            self._settings[k]=v.strip()
            if '#' in v:
                self._settings[k]=v[:v.find('#')]

        #[ prepare(k,v) for k,v in self._settings.items() ]

        self.doit()

    def doit(self):
        """ hack """
        global settings
        settings = self

    @property
    def app(self):
        """ derive flask app based on the combination of command-line
            options and the contents of the .ini files
        """
        return self._get_app()

    def _get_app(self):
        if self._app_cache: return self._app_cache
        ## set flask specific things that are non-optional
        error = lambda k: 'Fatal: You need to specify a "flask" section ' + \
                'with an entry like  "'+k+'=..." in your .ini file'
        try: app_name = self['flask']['app']
        except KeyError: raise SettingsError(error('app'))
        try: secret_key = self['flask']['secret_key']
        except KeyError: raise SettingsError(error('secret_key'))
        app = Flask(app_name)
        app.secret_key = secret_key

        ## set flask specific things that are optional
        flask_section = self['flask']
        if 'template_path' in flask_section:
            raise Exception,'niy'
            app.jinja_loader = FileSystemLoader(self['flask']['template_path'])
        if 'before_request' in flask_section:
            before_request = self['flask']['before_request']
            before_request = namedAny(before_request)
            app.before_request(before_request)
        if 'after_request' in flask_section:
            after_request = self['flask']['after_request']
            after_request = namedAny(after_request)
            app.after_request(after_request)

        if 'corkscrew.templates' in self:
            modules = self['corkscrew']['templates'].split(',')
            for module in modules:
                mdir = os.path.dirname(importlib.import_module(module).__file__)
                tdir = os.path.join(mdir, 'templates')
                if not os.path.exists(tdir):
                    report("template dir specified does not exist "+str(tdir))
                else:
                    if tdir not in app.jinja_loader.searchpath:
                        report('adding {t} to templates search',t=tdir)
                        app.jinja_loader.searchpath += [tdir]

        ## setup views
        self._installed_views = self._setup_views(app)
        #report('built urls: {u}',u=[v.url for v in views])
        reporting.console.draw_line()
        self._app_cache = app
        return app

    def _setup_views(self, app):
        """ NOTE: at this point app is only partially setup.
                  (do not attempt to use the app @property here)
        """
        corkscrew_section = self['corkscrew']
        try:
            view_holder = corkscrew_section['views']
        except KeyError:
            error = ('Fatal: could not find "view=<dotpath>" entry in the'
                     '[corkscrew] section of your .ini file')
            raise SettingsError(error)
        else:
            view_list = namedAny(view_holder)
            view_instances = []
            for v in view_list:
                try:
                    view_instances.append(v(app=app, settings=self))
                except Exception, e:
                    report('error working with view: '+str(v))
                    raise
            for v in view_instances:
                sub_views = v.install_into_app(app)
                view_instances += sub_views
            return view_instances

    def load(self, file, config={}):
        """ returns a dictionary with key's of the form
            <section>.<option> and the values
        """
        class MyConfigParser(configparser.ConfigParser):
            pass
        if not os.path.exists(file):
            raise SettingsError('ERROR: config file at "{f}" does not exist'.format(f=file))
        config = config.copy()
        cp = MyConfigParser()
        cp.read(file)
        return cp

    @property
    def runner(self):
        """ """
        user_section = self['user']
        corkscrew_section = self['corkscrew']
        if user_section['runner']:
            runner_dotpath = self['user.runner']
        else:
            try:
                runner_dotpath = self['corkscrew']['runner']
            except KeyError:
                warning = 'item "runner" not found in [flask] section, using naive runner'
                warnings.warn(warning)
                runner_dotpath = 'corkscrew.runner.naive_runner'
        try:
            runner = namedAny(runner_dotpath)
        except AttributeError:
            err="Could not find runner specified by dotpath: "+runner_dotpath
            raise AttributeError,err
        else:
            report("Using runner: {r}",r=runner_dotpath)
            return runner

    def shell_namespace(self):
        """ publish the namespace that's available to shell.
            subclasses should not forget to call super()!
        """
        return dict(app=self.app, settings=self)

    def run(self, *args, **kargs):
        """ this is a thing that probably does not belong in a
            settings abstraction, but it is very useful.. """
        if self.done: return

        if self._settings['user']['shell']:
            try:
                from IPython import Shell;
            except ImportError:
                raise SettingsError("You need IPython installed if you want to use the shell.")
            else:
                Shell.IPShellEmbed(argv=['-noconfirm_exit'],
                                   user_ns=self.shell_namespace())()

        else:
            app  = self.app
            port = int(self['flask']['port'])
            host = self['flask']['host']
            debug = self['flask']['debug'].lower()=='true'
            runner = self.runner
            runner(app=app, port=port, host=host, debug=debug)
            node = platform.node()


Settings = FlaskSettings

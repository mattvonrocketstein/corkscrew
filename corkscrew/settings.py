""" corkscrew.settings
"""

import os
import base64
import warnings
import importlib
import configparser

import humanize
import flask_sijax
from flask import Flask
from werkzeug import generate_password_hash
from corkscrew.reflect import namedAny

from report import report, console
from corkscrew.exceptions import SettingsError
from corkscrew import core

class Dictionaryish(object):
    def __contains__(self, other):
        """ dictionary compatability """
        return other in self._settings

    def __getitem__(self,k):
        """ dictionary compatability """
        return self._settings[k]

class FlaskSettings(Dictionaryish):
    """ combination option parser / settings parser for flask
        that reads the .ini format.
    """

    default_file = 'corkscrew.ini'
    jinja_globals = {}
    jinja_filters = {}

    def get_proxies(self):
        if 'proxy' in self:
            return dict(self['proxy'].items())
        return {}

    def get_redirects(self):
        if 'redirects' in self:
            return dict(self['redirects'].items())
        return {}

    @classmethod
    def get_parser(kls):
        """ build the default parser """
        from optparse import OptionParser
        parser = OptionParser()
        parser.set_conflict_handler("resolve")
        parser.add_option(
            "-c", default='',dest='cmd',
            help=("like python -c: \"a program passed in"
                  " as string (terminates option list)\""))
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

    def keys(self):
        return self._settings.keys()

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
        """ first load the default config so that overrides don't need
            to mention everything.  update default with the config
            specified by the command line optionparser, then
            update that with any other overrides delivered to the parser.
        """
        self._app_cache = None
        self._init_filename = filename
        self.options, self.args = self.get_parser().parse_args()

        # special case
        self.done = False
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
        """ total hack """
        global settings
        settings = self

    def get_schemas(self):
        """ """
        dotpath = self['corkscrew'].get('base_schema', None)
        if dotpath:
            BaseSchema = namedAny(dotpath)
            schemas = dict([[x.__name__, x] for x in BaseSchema.__subclasses__() ])
            return schemas
        return {}

    @property
    def app(self):
        """ derive flask app based on the combination of command-line
            options and the contents of the .ini files
        """
        return self._get_app()

    def _parse_autoindex(self, app):
        flask_section = self['flask']
        if 'autoindex' not in flask_section:
            raise RuntimeError('you do not have a setting for autoindex '
                               '(it is required even if it is empty).'
                               ' to continue, put "autoindex={}" in the '
                               '[flask]  of your .ini')
        else:
            from corkscrew.dir_index import DirView
            return DirView(app=app, settings=self)

    def _get_app(self):
        if self._app_cache: return self._app_cache
        ## set flask specific things that are non-optional
        error = lambda k: 'Fatal: You need to specify a "flask" section ' + \
                'with an entry like  "'+k+'=..." in your .ini file'
        try: app_name = self['flask']['app']
        except KeyError: raise SettingsError(error('app'))

        try: static_folder = os.path.expanduser(self['flask']['static_folder'])
        except KeyError: static_folder = 'static'

        app = Flask(app_name, static_folder=static_folder)
        self._setup_secret_key(app)

        ## set flask specific things that are optional
        flask_section = self['flask']
        corkscrew_section = self['corkscrew']

        self._parse_autoindex(app)

        if 'template_path' in flask_section:
            raise Exception,'deprecated'

        core._setup_pre_request(self, app)
        core._setup_post_request(self, app)
        core._setup_jinja_globals(self, app)
        self._setup_sijax(app)
        jinja_options = dict(app.jinja_options).copy()
        jinja_options['extensions'] += ['jinja2.ext.loopcontrols']
        if 'templates' in corkscrew_section:
            modules = corkscrew_section['templates'].split(',')
            for module in modules:
                mdir = os.path.dirname(importlib.import_module(module).__file__)
                tdir = os.path.join(mdir, 'templates')
                if not os.path.exists(tdir):
                    report("template dir specified does not exist "+str(tdir))
                else:
                    if tdir not in app.jinja_loader.searchpath:
                        report('adding {t} to templates search',t=tdir)
                        app.jinja_loader.searchpath += [tdir]

        else:
            report("WARNING! 'templates' entry not found in corkscrew section")

        ## setup views
        self._installed_views = core._setup_views(self, app)
        #report('built urls: {u}',u=[v.url for v in views])
        console.draw_line()
        app.template_filter()(humanize.naturaltime)
        app.template_filter()(humanize.naturaldate)
        #app.template_filter()(urlify_markdown)
        #app.template_filter()(markdown.markdown)

        self._app_cache = app

        return app

    def load(self, file, config={}):
        """ returns a dictionary with key's of the form
            <section>.<option> and the values
        """
        class MyConfigParser(configparser.ConfigParser):
            pass
        if not os.path.exists(file):
            raise SettingsError(
                'ERROR: config file at "{f}" does not exist'.format(f=file))
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
            # DEPRECATED..
            runner_dotpath = self['user.runner']
        else:
            try:
                runner_dotpath = corkscrew_section['runner']
            except KeyError:
                warning = 'item "runner" not found in [flask] section, using naive runner'
                warnings.warn(warning)
                runner_dotpath = 'corkscrew.runner.naive_runner'
        try:
            runner = core.namedAny(runner_dotpath)
        except AttributeError:
            err="Could not find runner specified by dotpath: "+runner_dotpath
            raise AttributeError(err)
        else:
            report("Using runner: {r}",r=runner_dotpath)
            return runner

    def get_views(self):
        dotpath = self['corkscrew']['views']
        views = namedAny(dotpath)
        views =  dict([[v.__name__, v] for v in views])
        return views

    def shell_namespace(self):
        """ publish the namespace that's available to shell.
            subclasses should not forget to call super()!
        """
        return dict(
            app=self.app, settings=self,
            schemas = self.get_schemas(),
            proxies = self.get_proxies(),
            redirects = self.get_redirects(),
            views = self.get_views())

    def pre_run(self):
        """ hook for subclassers.. """
        pass

    def run(self, *args, **kargs):
        """ this is a thing that probably does not belong in a
            settings abstraction, but it is very useful.. """
        self.pre_run()

        if self.options.cmd:
            ns = globals()
            ns.update(settings=self)
            exec self.options.cmd in self.shell_namespace()
            self.done = True

        if self.done: return

        if self._settings['user']['shell']:
            try:
                from smashlib import embed;
            except ImportError:
                raise SettingsError("You need smashlib installed "
                                    "if you want to use the shell.")
            else:
                embed(user_ns=self.shell_namespace())

        else:
            app  = self.app
            port = int(self['flask']['port'])
            report('running on port: {0}'.format(port))
            host = self['flask']['host']
            debug = self._setup_debug(app)
            runner = self.runner
            runner(app=app, port=port, host=host, debug=debug)

    def _setup_debug(self, app):
        from flask_debugtoolbar import DebugToolbarExtension
        debug = self['flask']['debug'].lower() in ['1','true']
        app.debug = debug
        if debug:
            report((".ini lists debug as true: "
                    "this setting will be migrated into flask"
                    "app & debugtoolbar will be turned on."))
            DebugToolbarExtension(app)
        return debug

    def _setup_mongo(self):
        var = '_mongo_setup_call'
        val = getattr(self, var, None)
        if val is not None:
            raise RuntimeError(
                "Called _setup_mongo twice?")
        port = ( self['mongo'].get('port') and \
                 int(self['mongo']['port'])) or \
                 None
        host = self['mongo'].get('host', 'localhost')
        db = self['mongo']['db_name']
        user = self['mongo'].get('username', None) or \
               self['mongo'].get('user', None) or \
               None
        pwd = self['mongo'].get('password', None) or \
              self['mongo'].get('pass', None) or \
              None
        if pwd:
            pwd = base64.decodestring(pwd)
        self.app.config["MONGODB_SETTINGS"] = dict(
            db=db, host=host, port=port,
            username=user, password=pwd)

        from flask.ext.mongoengine import MongoEngine
        db = MongoEngine(self.app)
        setattr(self, var, dict(port=port, host=host, db=db))

    def _setup_secret_key(self, app):
        err = ('use "secret_key" in the [flask] '
               'section of your ini, not "secretkey"')
        assert 'secretkey' not in self['flask'], err
        try: secret_key = str(self['flask']['secret_key'])
        except KeyError: raise SettingsError(err)
        app.secret_key = secret_key

    def _setup_sijax(self, app):
        ssp = os.path.join(app.static_folder, 'js', 'sijax')
        app.config['SIJAX_STATIC_PATH'] = ssp
        assert os.path.exists(ssp),"SIJAX_STATIC_PATH@'{0}' does not exist".format(ssp)
        app.config["SIJAX_JSON_URI"] = '/static/js/sijax/json2.js'
        report("sijax settings: \n  {0}".format(
            dict(SIJAX_STATIC_PATH=app.config['SIJAX_STATIC_PATH'],
                 SIJAX_JSON_URI = app.config['SIJAX_JSON_URI'])))
        flask_sijax.Sijax(app)

Settings = FlaskSettings

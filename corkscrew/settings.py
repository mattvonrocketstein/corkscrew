""" corkscrew.settings
"""

import os
import base64
import warnings
import importlib

import humanize
import flask_sijax
from flask import Flask
from flask.ext.mongoengine import MongoEngine
from werkzeug import generate_password_hash

from report import report, console
from goulash.settings import Settings as BaseSettings
from goulash.settings import SettingsError

import corkscrew
import corkscrew.core
from corkscrew.reflect import namedAny
from corkscrew.dir_index import DirView


class Overrides(BaseSettings):

    environ_key  = 'CORKSCREW_SETTINGS'
    default_file = 'corkscrew.ini'


    def get_parser(self):
        """ build the default parser """
        parser = super(Overrides, self).get_parser()
        parser.add_option("--port",  dest="port",
                          default='', help="server listen port")
        parser.add_option("--runner",  dest="runner",
                          default='', help="dotpath for app server")
        parser.add_option("--encode", dest='encode',
                          default="",
                          help="encode password hash using werkzeug")
        return parser

    def shell_namespace(self):
        """ publish the namespace that's available to shell.
            subclasses should not forget to call super()!
        """
        out = super(Overrides, self).shell_namespace()
        out.update(
            app=self.app, settings=self,
            schemas = self.get_schemas(),
            proxies = self.get_proxies(),
            redirects = self.get_redirects(),
            views = self.get_views())
        return out

    def show_version(self):
        super(Overrides, self).show_version()
        from corkscrew import __version__
        print 'corkscrew=={0}'.format(__version__)

    def run(self, *args, **kargs):
        """ this is a thing that probably does not belong in a
            settings abstraction, but it is very useful.. """
        finished = super(Overrides, self).run(*args, **kargs)
        if not finished:
            if self.options.encode:
                print generate_password_hash(self.options.encode)
                return
            app  = self.app
            port = int(self.get_setting('flask.port', insist=True))
            report('running on port: {0}'.format(port))
            host = self['flask']['host']
            debug = self._setup_debug(app)
            runner = self.runner
            runner(app=app, port=port, host=host, debug=debug)

    def __init__(self, filename=None):
        """ first load the default config so that overrides don't need
            to mention everything.  update default with the config
            specified by the command line optionparser, then
            update that with any other overrides delivered to the parser.
        """
        # this super call
        #   1) parses cli
        #   2) loads setting fil  based on env-vars/class-vars
        #   3) setup the implied `user` section
        super(Overrides, self).__init__(filename=filename)

        self._app_cache = None

        # a few command line options are allowed to override the .ini
        if self.options.port:
            self.update({'flask.port' : self.options.port})

        # update the implied user section
        self['user']['encode_password'] = self.options.encode
        self['user']['runner'] = self.options.runner
        corkscrew.SETTTINGS = self

class FlaskSettings(Overrides):
    """ combination option parser / settings parser for flask
        that reads the .ini format.
    """
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
            return DirView(app=app, settings=self)

    def _get_app(self):
        if self._app_cache: return self._app_cache
        ## set flask specific things that are non-optional
        error = lambda k: 'Fatal: You need to specify a "flask" section ' + \
                'with an entry like  "'+k+'=..." in your .ini file'
        app_name = self.get_setting('flask.app', insist=True)
        if app_name is None:
            raise SettingsError(error('app'))

        try: static_folder = os.path.expanduser(self['flask']['static_folder'])
        except KeyError: static_folder = 'static'

        app = Flask(app_name, static_folder=static_folder)
        self._setup_secret_key(app)

        ## set flask specific things that are optional
        flask_section = self['flask']
        corkscrew_section = self.get_section('corkscrew', insist=True)

        self._parse_autoindex(app)

        if 'template_path' in flask_section:
            raise Exception('deprecated')

        corkscrew.core._setup_pre_request(self, app)
        corkscrew.core._setup_post_request(self, app)
        corkscrew.core._setup_jinja_globals(self, app)
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
        self._installed_views = corkscrew.core._setup_views(self, app)
        #report('built urls: {u}',u=[v.url for v in views])
        console.draw_line()
        app.template_filter()(humanize.naturaltime)
        app.template_filter()(humanize.naturaldate)
        app.template_filter()(humanize.intcomma)
        #app.template_filter()(urlify_markdown)
        #app.template_filter()(markdown.markdown)
        self._app_cache = app
        return app

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
                err = ('item "runner" not found in [flask] '
                       'section, using naive runner')
                warnings.warn(err)
                runner_dotpath = 'corkscrew.runner.naive_runner'
        try:
            runner = corkscrew.core.namedAny(runner_dotpath)
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

    def _setup_debug(self, app):
        from flask_debugtoolbar import DebugToolbarExtension
        debug = self.get_setting('flask.debug', default='false')
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
        db = MongoEngine(self.app)
        setattr(self, var, dict(port=port, host=host, db=db))

    def _setup_secret_key(self, app):
        if 'secretkey' in self['flask']:
            err = ('use "secret_key" in the [flask] '
                   'section of your ini, not "secretkey"')
            raise SettingsError(err)
        secret_key = self.get_setting('flask.secret_key', insist=True)
        app.secret_key = secret_key

    def _setup_sijax(self, app):
        ssp = os.path.join(app.static_folder, 'js', 'sijax')
        app.config['SIJAX_STATIC_PATH'] = ssp
        if not os.path.exists(ssp):
            err = "SIJAX_STATIC_PATH@'{0}' does not exist, creating it"
            err = err.format(ssp)
            report(err)
            os.makedirs(ssp)
        app.config["SIJAX_JSON_URI"] = '/static/js/sijax/json2.js'
        report("sijax settings: \n  {0}".format(
            dict(SIJAX_STATIC_PATH=app.config['SIJAX_STATIC_PATH'],
                 SIJAX_JSON_URI = app.config['SIJAX_JSON_URI'])))
        flask_sijax.Sijax(app)

Settings = FlaskSettings

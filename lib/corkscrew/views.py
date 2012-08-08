""" corkscrew.views
"""
import os

import jinja2
import inspect

from flask import render_template
from flask import send_from_directory
from flask import request, jsonify, g, redirect
from report import report

def add_template_to_search_path(tpath, app):
    if not app:
        report('warning! app is null.  nonstandard init?')
        return
    if tpath not in app.jinja_loader.searchpath:
        report("Adding new template path: ",tpath)
        app.jinja_loader.searchpath += [tpath]


class FlaskView(object):
    """ FlaskView provides object-oriented view capabilities for flask,
        and encapsulates a few of the flask conventions and semantics
        into one package.
    """

    returns_json  = False
    methods       = ('GET',)
    requires_auth = False

    def __init__(self, app=None, settings=None):
        """ when instantiated, the view will let the app
             know about it's own urls.
        """

        self.__name__ = self.__class__.__name__.lower()
        self.settings = settings
        if app is not None:
            if self.url:
                app.add_url_rule(self.url, self.__name__, self,
                                 methods=self.methods)
        self.app = app

        if getattr(self, 'local_templates', False):
            tpath = os.path.dirname(inspect.getfile(self.__class__))
            tpath = os.path.join(tpath, 'templates')
            if not os.path.exists(tpath):
                err = 'local_templates is True for class, but no template directory exists'
                raise ValueError(err)
            add_template_to_search_path(tpath, self.app)

    def __call__(self):
        """ 1) honor ``requires_auth`` class var and
               redirects to login if necessary.
            2) honor ``returns_json`` class var and
               jsonify what is assumed to be a dictionary.
            3) dispatch based on get/post maybe ?
        """
        if self.requires_auth and not self.authorized:
            report('view requires authentication..redirecting to login',[self, g.user])
            return redirect('/login')
        result = self.main()
        if not result:
            report("WARNING: null result {0} given from {1}".format(result, self.main))
        if self.returns_json:
            result = jsonify(**result)
        return result

    def __mod__(self, other):
        """ self % var

            get an item out of the corkscrew settings dictionary
        """
        return self.settings[other]

    def __getitem__(self, k):
        """ self[var]

            proxy accessor for the current requests values
        """
        try:
            return request.values.get(k, None)
        except AttributeError:
            # when this happens from, say, a shell, the
            # LocalProxy for the request will malfunction
            # and that is unavoidable
            return None

    @property
    def user(self):
        """ proxy to flask's globals """
        return g.user

    @property
    def authorized(self):
        """ """
        return True if g.user else False

    def render_template(self, **kargs):
        """ shortcut that knows about this ``template`` class-var """
        kargs.update(authenticated = self.authorized)
        try:
            return render_template(self.template, **kargs)
        except jinja2.exceptions.TemplateNotFound:
            report('search order: {s}',
                   s=[ '/'.join(x.split('/')[-3:]) for x in self.app.jinja_loader.searchpath])
            raise

View = FlaskView


class SmartView(View):
    """ """
    pass

class Favicon(FlaskView):
    """ TODO: change to use settings  """
    url = '/favicon.ico'
    def main(self):
        return send_from_directory(os.path.join(self.app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')

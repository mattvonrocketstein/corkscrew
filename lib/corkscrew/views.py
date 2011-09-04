""" corkscrew.views
"""
import os

from flask import render_template
from flask import send_from_directory
from flask import request, jsonify, g, redirect
from report import report


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
        report('built view',self,self.url)

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
        return request.values.get(k, None)

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
        return render_template(self.template, **kargs)
View = FlaskView


class SmartView(View):
    """ """
    pass

class Favicon(FlaskView):
    """ doesn't work.  why?"""
    url = '/favicon.ico'
    def main(self):
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')

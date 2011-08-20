""" corkscrew.views
"""

from flask import request, jsonify, g, redirect
from flask import render_template

class FlaskView(object):
    """ FlaskView provides object-oriented view capabilities for flask,
        and encapsulates a few of the flask conventions and semantics
        into one package.
    """

    returns_json  = False
    methods       = ('GET',)
    requires_auth = False

    def __init__(self, app=None, settings=None):
        """ when instantiated, the view will let the app know about it's
            own urls.
        """
        self.__name__ = self.__class__.__name__.lower()
        self.settings = settings
        if app is not None:
            if self.url:
                app.add_url_rule(self.url, self.__name__, self,
                                 methods=self.methods)

    def __call__(self):
        """ """
        if self.requires_auth and not self.authorized:
            report('view requires authentication..redirecting to login',[self, g.user])
            return redirect('/login')
        result = self.main()
        if self.returns_json:
            result = jsonify(**result)
        return result

    def __getitem__(self, k):
        return request.values.get(k, None)

    @property
    def user(self):
        return g.user

    @property
    def authorized(self):
        """ """
        return True if g.user else False

    def render_template(self, **kargs):
        kargs.update(authenticated = self.authorized)
        return render_template(self.template, **kargs)
View = FlaskView

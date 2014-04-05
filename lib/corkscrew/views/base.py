""" corkscrew.views.base
"""

import flask
from flask import jsonify, g, redirect

from report import report

from corkscrew.blueprint import BluePrint
from corkscrew.util import use_local_template as _use_local_template

from .lazy import LazyView

class FlaskView(LazyView):
    """ FlaskView provides object-oriented view capabilities for flask,
        and encapsulates a few of the flask conventions and semantics
        into one package.
    """
    use_local_template = staticmethod(_use_local_template)
    redirect = staticmethod(flask.redirect)
    flash    = staticmethod(flask.flash)
    flask    = flask

    returns_json  = False
    methods       = ('GET',)
    requires_auth = False
    blueprint     = None

    def __init__(self, *args, **kargs):
        """ when instantiated, the view will let the app
            know about it's own urls.
        """
        super(FlaskView, self).__init__(*args, **kargs)
        ### this from blueprints now, but in the short term might need it for reference
        if self.blueprint is None:
            self.__class__.blueprint = BluePrint(
                self.__class__.__name__, self.__class__.__name__)

    @_use_local_template
    def render_error(self, msg):
        """ <font color=red>{{err}}</font> """
        return dict(err=msg)

    def install_into_app(v, app):
        """ TODO: returns a list of subviews that need work """
        # NOTE: think this does have to be done here instead of v.__init__
        assert v.blueprint
        if not v.blueprint.name:
            v.blueprint.name = v.__class__.__name__
        try:
            app.add_url_rule(v.url, v.__name__, v)
        except AssertionError:
            report("ERROR! adding view: {0}@{1}. url would have been {3}".format(
                v.__name__, v, v.url))
            raise
        app.register_blueprint(v.blueprint)
        return []

    def __str__(self):
        # FIXME HACK
        out = super(FlaskView, self).__str__()
        out = out.split('object at')[0].strip()
        return out+'>'

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
            try:
                result = jsonify(**result)
            except TypeError:
                raise TypeError(('{0} cannot JSONify "{1}", but '
                                 ' {0}.returns_json==True').format(self, result))
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
            return self.request.values.get(k, None)
        except AttributeError:
            # when this happens from, say, a shell, the
            # LocalProxy for the request will malfunction,
            # seems unavoidable
            return None

    @property
    def user(self):
        """ proxy to flask's globals """
        return g.user

View = FlaskView

class SmartView(View):
    """ smartviews are ones that might have their own
        templates embedded in docstrings.  (yes, i know
        you think this is a terrible idea.. dont care)
    """
    pass

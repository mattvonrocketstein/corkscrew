""" corkscrew.views
"""
import os

import jinja2
import inspect

import flask
from flask import abort
from flask import render_template
from flask import send_from_directory
from flask import request, jsonify, g, redirect
from report import report

from corkscrew.blueprint import BluePrint
from corkscrew.util import use_local_template

class LazyView(object):
    abort = abort
    def __init__(self, app=None, settings=None):
        """ when instantiated, the view will let the app
            know about it's own urls.
        """
        self.__name__ = self.__class__.__name__.lower()
        self.settings = settings
        self.app = app

    @property
    def request(self):
        return request

    @property
    def authorized(self):
        """ """
        return True if g.user else False

    def install_into_app(self, *args, **kargs):
        return []

    def render_template(self, **kargs):
        """ shortcut that knows about this ``template`` class-var """
        kargs.update(authenticated = self.authorized)
        try:
            return render_template(self.template, **kargs)
        except jinja2.exceptions.TemplateNotFound:
            report('search order: {s}',
                   s=[ '/'.join(x.split('/')[-3:]) \
                       for x in self.app.jinja_loader.searchpath ])
            raise
    render = render_template

class FlaskView(LazyView):
    """ FlaskView provides object-oriented view capabilities for flask,
        and encapsulates a few of the flask conventions and semantics
        into one package.
    """

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
        super(FlaskView,self).__init__(*args, **kargs)

        ### this from blueprints now, but in the short term might need it for reference
        if self.blueprint is None:
            raise TypeError,'FlaskView subclass must define a blueprint'

    def install_into_app(v,app):
        """ returns a list of subviews that need work """
        # NOTE: think this does have to be done here instead of v.__init__
        assert v.blueprint
        if not v.blueprint.name:
            v.blueprint.name = v.__class__.__name__
        #report('registering blueprint: ' + str([v.blueprint, v.url]))
        #v = v.blueprint.route(v.url)(v)
        #try:
        app.add_url_rule(v.url, v.__name__, v)
        #except Exception,e:
        #report("error adding view: "+str(v))
            #print 'error adding url rule'
            #from IPython import Shell; Shell.IPShellEmbed(argv=['-noconfirm_exit'])()
            #raise
        app.register_blueprint(v.blueprint)
        return []

    def __str__(self):
        # FIXME HACK
        out = super(FlaskView,self).__str__()
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

View = FlaskView

class SmartView(View):
    """ smartviews are ones that might have their own
        templates embedded in docstrings.  (yes, i know
        you think this is a terrible idea, i dont care)
    """
    pass

class Favicon(FlaskView):
    """ TODO: change to use settings  """
    url = '/favicon.ico'
    blueprint = BluePrint('favicon', __name__)
    def main(self):
        return send_from_directory(os.path.join(self.app.root_path, 'static'),
                                   'favicon.ico',
                                   mimetype='image/vnd.microsoft.icon')

class SettingsView(View):
    url = '/__settings__'
    blueprint = BluePrint('settings', __name__)
    requires_auth = True
    requires_auth = True

    @use_local_template
    def main(self):
        """
        <table>
          <tr>
            <td><b>root</b></td><td>{{rootpath}}</td>
          </tr>
        </table>
        """
        return dict(rootpath=self.app.root_path)

class ListViews(View):
    url = '/__views__'
    blueprint=BluePrint('views', __name__)
    requires_auth = True
    @use_local_template
    def main(self):
        """
        {# renders a list of all views.. #}
        <table>
          <tr>
             <td>view</td>
             <td>url</td>
             <td>from module</td>

          </tr>
          <tr><td colspan=4> <hr/></td></tr>
          {% for v in views %}
          <tr>
            <td><b>{{v.__name__}}</b></td>
            <td><i>{{v.url}}</i></td>
            <td><small>{{v.__class__.__module__}}<small></td>
          </tr>
          {%endfor%}
        </table>
        """
        # TODO: might as well organize 'views' by schema
        return dict(views=self.settings._installed_views)

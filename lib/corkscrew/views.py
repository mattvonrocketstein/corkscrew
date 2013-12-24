""" corkscrew.views
"""
import os

import jinja2
import inspect

import flask
from flask import abort
from flask import render_template
from flask import request, jsonify, g, redirect
from report import report

from corkscrew.blueprint import BluePrint
from corkscrew.util import use_local_template

class LazyView(object):
    abort = abort
    report = staticmethod(report)
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
        super(FlaskView, self).__init__(*args, **kargs)

        ### this from blueprints now, but in the short term might need it for reference
        if self.blueprint is None:
        #if self.__class__.blueprint is None:
            self.__class__.blueprint = BluePrint(self.__class__.__name__,
                                                 self.__class__.__name__)
            #raise TypeError, 'FlaskView subclass must define a blueprint'

    @use_local_template
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
        you think this is a terrible idea.. dont care)
    """
    pass

from .favicon import Favicon

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

class FourOhFourView(LazyView):

    template = 'page_not_found.html'

    def __init__(self, *args, **kargs):
        super(FourOhFourView, self).__init__(*args, **kargs)

        @self.app.errorhandler(404)
        def not_found(error):
            return self.render(), 404

class SijaxView(View):

    @property
    def sijax(self):
        from flask import g
        return g.sijax

    @property
    def is_sijax(self):
        return self.sijax.is_sijax_request

    def install_into_app(self, app):
        import flask_sijax
        flask_sijax.route(self.app, self.url)(self.main)
        return []

class SijaxDemo(SijaxView):

    url = '/comet'

    def comet_do_work_handler(self, obj_response, sleep_time):
        import time
        for i in range(6):
            width = '%spx' % (i * 80)
            obj_response.css('#progress', 'width', width)
            obj_response.html('#progress', "x-"+str(i))
            # Yielding tells Sijax to flush the data to the browser.
            # This only works for Streaming functions (Comet or Upload)
            # and would not work for normal Sijax functions
            yield obj_response
            if i != 5:
                time.sleep(sleep_time)

    @use_local_template
    def main(self):
        """
        <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.5.1/jquery.min.js"></script>
        <script type="text/javascript" src="/static/js/sijax/sijax.js"></script>
        <script type="text/javascript" src="/static/js/sijax/sijax_comet.js"></script>
        <script type="text/javascript">{{ g.sijax.get_js()|safe }}</script>
        <pre>{{g.sijax.get_js()}}</pre>
        <div id="progressWrapper"><div id="progress" style=""></div></div>
        <button id="btnStart">Start</button>
        <script type="text/javascript">
        $('#btnStart').bind('click', function () {
            $('#progress').css('width', 0).html('&nbsp;');
            sjxComet.request('do_work', [1]);});
        </script>
        """
        if self.is_sijax:
            # The request looks like a valid Sijax request
            # Let's register the handlers and tell Sijax to process it
            self.sijax.register_comet_callback('do_work', self.comet_do_work_handler)
            out = self.sijax.process_request()
            return out
        return dict()

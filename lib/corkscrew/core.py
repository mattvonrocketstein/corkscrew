""" corkscrew.core
"""
from report import report
from corkscrew.reflect import namedAny
from corkscrew.exceptions import SettingsError

def _setup_pre_request(settings, app):
    flask_section = settings['flask']
    if 'before_request' in flask_section:
        before_request = settings['flask']['before_request']
        before_request = namedAny(before_request)
        app.before_request(before_request)

def _setup_views(settings, app):
    """ NOTE: at this point app is only partially setup.
        (do not attempt to use the app @property here)
    """
    corkscrew_section = settings['corkscrew']
    try:
        view_holder = corkscrew_section['views']
    except KeyError:
        error = ('Fatal: could not find "views=<dotpath>" entry in the'
                 '[corkscrew] section of your .ini file')
        raise SettingsError(error)
    else:
        view_list = namedAny(view_holder)
        view_instances = []
        for v in view_list:
            try:
                view_instances.append(v(app=app, settings=settings))
            except Exception:
                report('error working with view: '+str(v))
                raise
        for v in view_instances:
            sub_views = v.install_into_app(app)
            view_instances += sub_views
        return view_instances

def _setup_post_request(settings, app):
    flask_section = settings['flask']
    if 'after_request' in flask_section:
        after_request = settings['flask']['after_request']
        after_request = namedAny(after_request)
        app.after_request(after_request)

def _setup_jinja_globals(settings, app):
    app.jinja_env.globals.update(**settings.jinja_globals)
    app.jinja_env.filters.update(**settings.jinja_filters)

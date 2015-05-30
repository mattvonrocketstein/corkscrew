""" corkscrew.core
"""
from report import report
from corkscrew.reflect import namedAny

def _setup_pre_request(settings, app):
    """ """
    #flask_section = settings.get_section('flask', insist=True)
    before_request = settings.get_setting('flask.before_request')
    if before_request is not None:
        before_request = namedAny(before_request)
        app.before_request(before_request)

def _setup_views(settings, app):
    """ NOTE: at this point app is only partially setup.
        (do not attempt to use the app @property here)
    """
    #corkscrew_section = settings.get_section('corkscrew', insist=True)
    view_holder = settings.get_setting('corkscrew.views',insist=True)

    view_list = namedAny(view_holder)
    view_instances = []
    for v in view_list:
        view_instances.append(v(app=app, settings=settings))
    for v in view_instances:
        try:
            sub_views = v.install_into_app(app)
        except Exception:
            report("View is broken! ", v)
            raise
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

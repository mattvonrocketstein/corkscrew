""" corkscrew.views.lazy
"""

import jinja2
from flask import abort
from flask import render_template
from flask import request, g
from flask import render_template_string

from report import report


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

    def get_ctx(self, **kargs):
        kargs.update(authenticated = self.authorized)
        # setup extra scripts
        extra_scripts = kargs.pop('extra_scripts', [])
        extra_scripts += getattr(self, 'extra_scripts', [])
        kargs['extra_scripts'] = extra_scripts
        # setup extra javascript
        javascript = kargs.pop('javascript', '')
        if hasattr(self, 'javascript') and \
           isinstance(self.javascript, basestring):
            javascript+='\n'+self.javascript
        kargs['javascript'] = javascript
        kargs['__view__'] = self
        return kargs

    def get_template(self, fname):
        return self.app.jinja_env.get_template(fname)

    def render_template(self,*args, **kargs):
        """ shortcut that knows about this ``template`` class-var. """
        tmp = self.get_ctx()
        tmp.update(kargs)
        kargs = tmp
        if args:
            assert len(args)==1 and isinstance(args[0], basestring)
            return render_template_string(args[0], **kargs)
        try:
            return render_template(self.template, **kargs)
        except jinja2.exceptions.TemplateNotFound:
            report('search order: {s}',
                   s = [ '/'.join(x.split('/')[-3:]) \
                         for x in self.app.jinja_loader.searchpath ])
            raise
    render = render_template

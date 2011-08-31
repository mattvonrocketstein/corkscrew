""" corkscrew.auth
"""
from werkzeug import check_password_hash, generate_password_hash
import jinja2

from flask import render_template, g, flash
from flask import request, session, redirect

from corkscrew import View

import report as reporting
report = reporting.report

class AuthCommon(View):
    def auth_redirect(self):
        _next = request.referrer
        if not _next or self.url in _next:
            _next = self%'corkscrew.default_auth_next'
            return redirect(_next)

class Logout(AuthCommon):
    """Logs the user out."""
    url     = '/logout'
    methods = ["GET"]

    def main(self):
        flash('You were logged out')
        session.pop('user_id', None)
        return self.auth_redirect()

class Login(AuthCommon):
    """ Logs the user in.

        TODO: send them back where they came from, and not to /
    """
    url      = '/login'
    methods  = methods = ["GET", "POST"]
    template = 'login.html'

    def template_literal(self, t):
        self._template = t

    def __invert__(self):
        """ give the template literal if present. """
        return self._template

    def render_template(self, *args, **kargs):
        try:
            return super(self.__class__,self).render_template(*args, **kargs)
        except jinja2.exceptions.TemplateNotFound,e:
            from flask.templating import _request_ctx_stack,_render
            t = jinja2.Template(self._template)
            import copy
            t.loader='hahaha'
            #t.environment = copy.copy(self.app.jinja_env)
            #t.environment.loader=self.app.jinja_loader
            #from IPython import Shell; Shell.IPShellEmbed(argv=['-noconfirm_exit'])()
            ctx = _request_ctx_stack.top
            ctx.app.update_template_context(kargs)
            return _render(t, kargs, ctx.app)


    def main(self):
        """ """
        if self.authorized:
            report('already authorized', self.user)
            return self.auth_redirect()

        if request.method == 'POST':
            users = self.settings%'users'
            user = self['username']
            if user not in users:
                return self.render_template(error='Invalid username')
            if not check_password_hash(users[user],self['password']):
                return self.render_template(error='Invalid password')
            else:
                flash('You were logged in')
                session['user_id'] = user
                return self.auth_redirect()
        return self.render_template()

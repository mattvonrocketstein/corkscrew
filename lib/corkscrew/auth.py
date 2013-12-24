""" corkscrew.auth
"""
from werkzeug import check_password_hash, generate_password_hash
import jinja2

from flask import render_template, g, flash
from flask import request, session, redirect

from corkscrew import View
from corkscrew.blueprint import BluePrint

import report as reporting
report = reporting.report

class AuthCommon(View):
    def auth_redirect(self):
        _next = self['next'] or request.referrer
        if not _next or self.url in _next:
            _next = self.settings['corkscrew']['default_auth_next']
        return redirect(_next)

class Logout(AuthCommon):
    """Logs the user out."""
    url     = '/logout'
    methods = ["GET"]
    blueprint = BluePrint('logout', __name__)
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
    blueprint = BluePrint('login', __name__)

    def __invert__(self):
        """ give the template literal if present. """
        return self._template

    def render_template(self, *args, **kargs):
        """ variation of View.render_template that prefers
            ``self.template`` on the filesystem, and failing
            that will use an embedded template literal at
            ``self._template``
        """
        try:
            return super(self.__class__,self).render_template(*args, **kargs)
        except jinja2.exceptions.TemplateNotFound, e:
            from flask.templating import render_template_string
            report("template {T} not found, using literal",T=self.template)
            return render_template_string(self._template, **kargs)

    def main(self):
        """ """
        if self.authorized:
            report('already authorized', self.user)
            return self.auth_redirect()

        if request.method == 'POST':
            users = self.settings['users']
            user = self['username']
            next = self['next']
            if user not in users:
                #print __file__,':valid users:', users
                return self.render_template(error='Invalid username')
            if not check_password_hash(users[user],self['password']):
                return self.render_template(error='Invalid password')
            else:
                flash('You were logged in')
                session['user_id'] = user
                return self.auth_redirect()
        return self.render_template()

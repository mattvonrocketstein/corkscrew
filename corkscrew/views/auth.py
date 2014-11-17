""" corkscrew.views.auth
"""
from werkzeug import check_password_hash
import jinja2

from flask import flash
from flask import request, session, redirect

from corkscrew.views.base import View
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
    _template = (
        """
        {% extends "layout.html" %}
        {% block title %}Sign In{% endblock %}
        {% block body %}
        <h2>Sign In</h2>
        {% if error %}
        <div class=error><strong>Error:</strong> {{ error }}</div>
        {% endif %}
        <form action="" method=post>
        <dl>
        <dt>Username:
        <dd>
        <input type=text
        name=username size=30 value="{{request.form.username}}">
        <dt>Password:
        <dd><input type=password name=password size=30>
        <input type=hidden name=next value="{{request.values.next}}">
        </dl>
        <div class=actions><input type=submit value="Sign In"></div>
        </form>
        {% endblock %}
        """)

    def render_template(self, *args, **kargs):
        """ variation of View.render_template that prefers
            ``self.template`` on the filesystem, and failing
            that will use an embedded template literal at
            ``self._template``
        """
        try:
            return super(self.__class__,self).render_template(*args, **kargs)
        except jinja2.exceptions.TemplateNotFound:
            from flask.templating import render_template_string
            err = "template@\"{T}\" not found, using literal"
            err = err.format(T=self.template)
            report(err)
            assert self._template is not None, "No login template on filesystem or in class!"
            return render_template_string(self._template, **kargs)

    def main(self):
        """ """
        if self.authorized:
            report('already authorized', self.user)
            return self.auth_redirect()

        if request.method == 'POST':
            users = self.settings['users']
            user = self['username']
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

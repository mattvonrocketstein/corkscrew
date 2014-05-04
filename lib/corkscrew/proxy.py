""" corkscrew.proxy
"""

import urllib2
from goulash.cache import cached
from .views import FlaskView

class ProxyView(FlaskView):
    """ subclass me and define proxy_url """
    proxy_url = None
    cache_timeout = 60*10

    def __init__(self, *args, **kargs):
        super(ProxyView, self).__init__(*args, **kargs)
        self.main = cached(self.proxy_url, timeout=self.cache_timeout)(self.main)

    def main(self):
        return urllib2.urlopen(self.proxy_url).read()


class RedirectView(FlaskView):
    """ subclass me and define proxy_url """
    proxy_url = None

    def main(self):
        return self.redirect(self.proxy_url)

class ViewsFromSettings(FlaskView):
    def install_into_app(self, app):
        out = []
        subsection = self.settings[self.settings_subsection]
        if not subsection:
            self.report("WARNING: No subsection for {0}".format(self.settings_subsection))
            from IPython import Shell; Shell.IPShellEmbed(argv=['-noconfirm_exit'])()
        for local_url in subsection:
            proxy_url = subsection[local_url]
            name = 'Dynamic{0}:{1}'.format(self.settings_subsection, local_url)
            View = type(name,
                        (self.concrete_view_class,), dict(proxy_url=proxy_url, url=local_url))
            view = View(app=app, settings=self.settings)
            view.install_into_app(app)
            out.append(view)
        return out

class ProxyFromSettings(ViewsFromSettings):
    """ interprets [proxy] section of .ini config
        and adds whatever proxies you want.

        this view is meta, has no url of it's own, and
        only exists to create subviews. each entry will
        in the .ini section will create a ProxyView
        subview. example .ini section follows:

           [proxy]
           /local/google=http://google.com

    """
    concrete_view_class = ProxyView
    settings_subsection = 'proxy'

class RedirectsFromSettings(ViewsFromSettings):
    concrete_view_class = RedirectView
    settings_subsection = 'redirects'

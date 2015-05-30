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
        subsection = self.settings.get_section(
            self.settings_subsection, insist=True)
        local_urls = [x for x in subsection.keys() if x.startswith('/')]
        for local_url in local_urls:
            proxy_url = subsection[local_url]
            # generate an excruciatingly ugly class name here,
            # because flask wants it to be unique.
            kls_name = 'DynamicViewFromSettings_{0}_{1}'
            kls_name = kls_name.format(self.settings_subsection,
                                       local_url.replace('/',''))
            kls_doc = ("ProxyView, generated from settings .ini,"
                       " where (local,remote) is ({0}, {1})")
            kls_doc = kls_doc.format(local_url, proxy_url)
            kls_namespace = dict(
                __doc__=kls_doc,
                proxy_url=proxy_url,
                url=local_url)
            kls_bases = (self.concrete_view_class, )
            View = type(kls_name, kls_bases, kls_namespace)
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

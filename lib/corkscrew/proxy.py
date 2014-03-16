from .views import FlaskView

import urllib2
from goulash.cache import cached

class ProxyView(FlaskView):
    """ subclass me and define proxy_url """
    proxy_url = None
    cache_timeout = 60*10

    def __init__(self, *args, **kargs):
        super(ProxyView, self).__init__(*args, **kargs)
        self.main = cached(self.proxy_url, timeout=self.cache_timeout)(self.main)

    def main(self):
        return urllib2.urlopen(self.proxy_url).read()

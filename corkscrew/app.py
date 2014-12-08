""" corkscrew.app

    TODO: better name instead of overloading "app" again..
"""
class App(object):
    def __init__(self, name='No name',
                 url = '/no_url_given_for_app',
                 use_image=None,
                 requires_unauth=False,
                 requires_auth=False):
        self.name, self.url = name, url
        self.requires_auth = requires_auth
        self.requires_unauth = requires_unauth
        self.use_image = use_image

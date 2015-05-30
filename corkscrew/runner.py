""" corkscrew.runner
"""

import os
import signal
from importlib import import_module

from report import report
from goulash.python import expanduser

import corkscrew

class if_importable:
    """ decorator to conditionally define a function """
    def __init__(self, module_name, error='Could not import {module}.'):
        self.module_name=module_name
        self.base_error = error

    def __call__(self, func, msg=''):
        """ """
        try:
            import_module(self.module_name)
        except ImportError:
            return self.error_runner(msg)
        else:
            return func

    def error_runner(self, msg=''):
        """ constructs a fake runner that will die with the given error message. """
        base_error = "Cannot comply with invocation request.. "
        msg = msg or self.base_error.format(module=self.module_name)
        msg = base_error + msg
        def new_func(*args, **kargs):
            raise RuntimeError(msg)
        return new_func

@if_importable('tornado')
def tornado(app=None, host=None, port=None, debug=None):
        """ copied from the tornado runner reccomended in flask docs """
        from tornado.wsgi import WSGIContainer
        from tornado.httpserver import HTTPServer
        from tornado.ioloop import IOLoop
        container   = WSGIContainer(app)
        http_server = HTTPServer(container)
        http_server.listen(port)
        IOLoop.instance().start()

def flask(app=None, host=None, port=None, debug=None):
    """ the flask default runner.  (which is itself a thin
        wrapper around stuff in the werkzeug.serving
        module)
    """
    return app.run(host=host,
                   port=port,
                   debug=debug)
# this is the default runner used by corkscrew.settings
naive_runner = flask

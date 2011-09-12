""" corkscrew.runners
"""


from importlib import import_module
class if_importable:
    def __init__(self, module_name, error='Could not import {module}.'):
        self.module_name=module_name
        self.base_error = error

    def __call__(self, func, msg=''):
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
        msg = base_error+msg
        def new_func(*args, **kargs):
            raise RuntimeError, msg
        return new_func

@if_importable('tornado')
def tornado_runner(app=None, host=None, port=None, debug=None):
        """ copied from the tornado runner reccomended in flask docs """
        from tornado.wsgi import WSGIContainer
        from tornado.httpserver import HTTPServer
        from tornado.ioloop import IOLoop
        container   = WSGIContainer(app)
        http_server = HTTPServer(container)
        http_server.listen(port)
        IOLoop.instance().start()

def naive_runner(app=None,host=None,port=None,debug=None):
    """ the flask default runner """
    return app.run(host=host,
                   port=port,
                   debug=debug)

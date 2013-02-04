""" corkscrew.runners
"""

import os
import signal
from importlib import import_module

from report import report
from corkscrew.settings import settings

def write_pid_file():
    """ write the pidfile """
    pid_file = settings['corkscrew.pid_file']
    if os.path.abspath(pid_file) != pid_file:
        err = 'Please use absolute path for "pid_file" entry in [corkscrew] section'
        raise RuntimeError(err)
    else:
        if os.path.exists(pid_file):
            with open(pid_file,'r') as fhandle:
                try:
                    pid = int(fhandle.read().strip())
                except ValueError:
                    pid = None
            report('killing pid {p}', p=pid)
            if pid is not None:
                try:
                    os.kill(pid, signal.SIGKILL)
                except OSError,e:
                    if 'No such process' in str(e):
                        pass
                    else:
                        raise
        with open(pid_file,'w') as fhandle:
            new_pid = str(os.getpid())
            fhandle.write(new_pid)
        report('this pid is {p}', p=new_pid)

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
            raise RuntimeError, msg
        return new_func

@if_importable('tornado')
def tornado(app=None, host=None, port=None, debug=None):
        """ copied from the tornado runner reccomended in flask docs """
        from tornado.wsgi import WSGIContainer
        from tornado.httpserver import HTTPServer
        from tornado.ioloop import IOLoop
        container   = WSGIContainer(app)
        write_pid_file()
        http_server = HTTPServer(container)
        http_server.listen(port)
        IOLoop.instance().start()

def flask(app=None, host=None, port=None, debug=None):
    """ the flask default runner """
    return app.run(host=host,
                   port=port,
                   debug=debug)

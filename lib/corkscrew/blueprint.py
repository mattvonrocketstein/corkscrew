""" corkscrew.blueprint
"""

import os, uuid

from flask import Blueprint
from report import report

def generate_name():
    return '' #os.popen('uuidgen -t').read().strip()

class BluePrint(Blueprint):
    def __repr__(self):
        msg = '<{0}.{1} "{2}" from {3}>'
        msg = msg.format(self.__class__.__module__,
                         self.__class__.__name__,
                         self.name, self.import_name)
        return msg

    def __init__(self, first, *args, **kargs):
        name, import_name= None, None
        if args:
            second = args[0]
            args = args[1:]
        else:
            second = None

        if first and not second:
            # (only given import_name)
            name = generate_name()
            import_name = first

        if first and second:
            name = first
            import_name = second

        try:
            super(BluePrint,self).__init__(name, import_name, *args, **kargs)
        except ImportError,e:
            # nonstandard init like --shell, etc
            report("squashing import error: "+str(e))
            super(BluePrint,self).__init__(str(uuid.uuid1()),__name__)

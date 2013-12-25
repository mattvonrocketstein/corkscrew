""" corkscrew.util
"""
import os
from flask import render_template_string

from report import report

opj = os.path.join
ope = os.path.exists
isdir = os.path.isdir

def use_local_template(func):
    """ example usage:

          @use_local_template
          def main(self):
              ''' this docstring will be used as a template '''
              return dict(this_context_will_be_used='to render the template')
    """
    def fxn(*args, **kargs):
        old = func(*args, **kargs)
        self = list(args).pop(0)
        context = self.get_ctx()
        if not isinstance(old, dict):
            # it might be a redirect or something
            report("use_local_template does not return a dictionary.. passing it thru",
                   context)
            return old
        else:
            context = context.update(**old)
        template = '{%extends "layout.html" %}{%block body%}' + \
                   func.__doc__ + '{%endblock%}'
        return render_template_string(template, **context)
    return fxn

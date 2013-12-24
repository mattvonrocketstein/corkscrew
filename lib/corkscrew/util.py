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
        context = func(*args, **kargs)
        if not isinstance(context, dict):
            report("use_local_template does not return a dictionary.. passing it thru")
            return context
        template = '{%extends "layout.html" %}{%block body%}<center>' + \
                   func.__doc__ + '</center>{%endblock%}'
        return render_template_string(template, **context)
    return fxn

""" corkscrew.util
"""
from flask import render_template_string

def use_local_template(func):
    """ example usage:

          @use_local_template
          def main(self):
              ''' this docstring will be used as a template '''
              return dict(this_context_will_be_used='to render the template')
    """
    def fxn(*args, **kargs):
        context = func(*args, **kargs)
        template = '{%extends "layout.html" %}{%block body%}<center>' + \
                   func.__doc__ + '</center>{%endblock%}'
        return render_template_string(template, **context)
    return fxn

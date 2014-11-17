""" corkscrew.views.json_edit
"""
from corkscrew.views import View


class JSONEdit(View):
    url = '/json_editor'
    template = 'json_editor.html'
    def get_json(self):
        raise Exception,'subclassers should override this method'

    def get_ctx(self):
        extra_scripts = [
            # jquery.min.js is implied here
            '/static/js/json2.js',
            '/static/js/jquery.jsoneditor.js',
            '/static/js/jsoneditor.js',]
        extra_css = ["/static/css/jsoneditor.css" ]
        return dict(
            json = self.get_json(),
            extra_css = extra_css,
            extra_scripts=extra_scripts )

    def main(self):
        t = self.get_template(self.template)
        ctx = self.get_ctx()
        string = t.render(**ctx)
        if self['ajax']:
            header = '{% extends "base_ajax.html" %}'
        else:
            header = '{% extends "layout.html" %}'
            string = '{%block body%}' + \
                     string + '{%endblock%}'
        string = header + string
        t = self.app.jinja_env.from_string(string)
        string = t.render(**ctx)
        return string

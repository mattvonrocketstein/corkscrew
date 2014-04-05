""" corkscrew.views.json_edit
"""
from corkscrew.views import View
from jinja2 import Template

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
        return dict(
            json = self.get_json(),
            extra_css = [
                "/static/css/jsoneditor.css" ],
            extra_scripts=extra_scripts )

    def main(self):
        t = self.get_template(self.template)
        ctx=self.get_ctx()
        string = t.render(**ctx)
        if self['ajax']:
            string='{% extends "base_ajax.html" %}'+string
        else:
            string='{% extends "layout.html" %}{%block body%}'+string+'{%endblock%}'
        t = self.app.jinja_env.from_string(string)
        string = t.render(**ctx)
        return string

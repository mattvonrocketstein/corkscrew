""" corkscrew.demo.views
"""

from corkscrew.views import FlaskView, use_local_template

class Home(FlaskView):
    url = '/'

    @use_local_template
    def main(self):
        """
        <strong>various demos</strong>
        <table style="margin-left:15px">
            {% for k,v in demos.items()%}
            <tr><td><b><a href="{{k}}">{{k}}</a></b></td><td><{{v}}</a></td></tr>
            {%endfor%}
        </table><hr>
        <strong>app metatdata</strong>
        <table style="margin-left:15px">
            {% for k,v in app_metadata.items()%}
            <tr><td><b>{{k}}</b></td><td>{{v}}</td></tr>
            {%endfor%}
        </table><hr>
        """
        #from IPython import Shell; Shell.IPShellEmbed(argv=['-noconfirm_exit'])()
        return dict(
            demos={
                '/comet':'comet demo (via sijax)',
                '/json_editor':'json editor',
                },
            app_metadata=dict(
                static_folder=self.app.static_folder,
                jinja_env_globals=self.app.jinja_env.globals.keys(),
                rootpath=self.app.root_path))

class JSONEdit(FlaskView):
    url = '/json_editor'

    @use_local_template
    def main(self):
        """
        <script src="/static/js/json2.js"></script>
        <script src="/static/js/jquery.min.js"></script>
        <script src="/static/js/jquery.jsoneditor.js"></script>
        <script src="/static/js/jsoneditor.js"></script>
        <link rel="stylesheet" href="/static/css/jsoneditor.css"/>
        <a href=# id="expander">Expand all</a>
        <table border=1 width=100%>
        <tr>
        <td><div id="editor" class="json-editor"></div></td>
        <td><textarea id="json"></textarea></td>
        </tr>
        </table>
        """
        return dict()
from corkscrew.comet import SijaxDemo
__views__ = [
    Home,
    JSONEdit,
    SijaxDemo
    ]

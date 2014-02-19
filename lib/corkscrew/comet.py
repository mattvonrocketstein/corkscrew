""" corkscrew.comet
"""

import time
import demjson
import threading

from goulash.stdout import ThreadedStdout
from goulash.ansi import Ansi2HTMLConverter

from corkscrew.views import View
from corkscrew.util import use_local_template

class SijaxView(View):
    """ very basic corkscrew integration with sijax """

    @property
    def sijax(self):
        from flask import g
        return g.sijax

    @property
    def is_sijax(self):
        return self.sijax.is_sijax_request

    def install_into_app(self, app):
        import flask_sijax
        flask_sijax.route(self.app, self.url)(self.main)
        return []

class CometWorker(SijaxView):
    """ to use this class, simply"""
    extra_scripts = [ '/static/js/sijax/sijax.js',
                      '/static/js/sijax/sijax_comet.js',
                      ]

    def __init__(self, *args, **kargs):
        super(CometWorker, self).__init__(*args, **kargs)
        self.stdout = ThreadedStdout()
        self.stdout.install()

    def comet_handler(self, obj_response, bonk):
        """ """
        bonk = demjson.decode(bonk)
        conv = Ansi2HTMLConverter(inline=False, escaped=False)
        unansi = conv.convert
        obj_response.html_append('#comet_data', conv.get_style())
        thr = threading.Thread(target=lambda: self.worker(**bonk), name='testing')
        q = self.stdout.register(thr)
        thr.start()

        hidebusy = lambda:obj_response.css('#loading_icon', 'display', 'none')
        showbusy = lambda:obj_response.css('#loading_icon', 'display', 'block')

        def read():
            zult = self.stdout.read_all(thr).replace('\n','<br/>')
            if zult:
                zult = unansi(zult)
                obj_response.html_append('#comet_data', zult)
                hidebusy()
            else:
                showbusy()

        while thr.is_alive():
            read()
            yield obj_response
            time.sleep(.5)
        read()
        hidebusy()
        yield obj_response

    def main(self):
        """
        {%extends "layout.html" %}
        {%block body%}
        <script type="text/javascript">
        {{ g.sijax.get_js()|safe }}
        </script>

        <table><tr>
        <td>{%if not autostart%}<button id="btnStart">Start</button>{%endif%}</td>
        <td><img id="loading_icon" src="{{loading_icon}}"></td>
        </tr></table>
        <div id="comet_data" style=""></div>
        <script type="text/javascript">
        var bonk='{{bonk}}';
        {%if not autostart%}
        $('#btnStart').bind('click', function(){sjxComet.request('do_work', [bonk]);});
        {%else%}
        $(document).ready(function(){sjxComet.request('do_work');});
        {%endif%}
        $('#loading_icon').hide();
        </script>
        {%endblock%}
        """
        self.request_data = dict(self.request.args.items())
        if self.is_sijax:
            self.sijax.register_comet_callback('do_work', self.comet_handler)
            out = self.sijax.process_request()
            return out
        else:
            return self.render(
                CometWorker.main.__doc__,
                javascript=self.sijax.get_js(),
                autostart=self['start'],
                bonk=demjson.encode(self.request_data),
                loading_icon='/static/img/loading.gif',)

class SijaxDemo(CometWorker):

    url = '/comet'

    def worker(self, **kargs):
        for x in 'hello world':
            print x,
            time.sleep(1)

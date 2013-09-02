""" corkscrew.dir_index
"""
import os
import demjson
from flask.ext.silk import Silk
from flask.ext.autoindex import AutoIndex, RootDirectory
from corkscrew.views import FlaskView
from corkscrew.util import isdir, ope
def _install_index(app, filepath, url):
    kargs = dict(add_url_rules=False)
    idx   = AutoIndex(app, filepath, **kargs)
    @app.route(url)
    @app.route(url+'<path:path>')
    def autoindex(path='/'):
        return idx.render_autoindex(path)
    return idx

# NB: almost like the signature for a FlaskView, but left as a
#     function because it should not require "self.blueprint"
def DirView(app=None, settings=None, **kargs):
    flask_section=settings['flask']
    autoindex_cfg = flask_section['autoindex']
    autoindex_cfg = demjson.decode(autoindex_cfg)
    for url, filepath in autoindex_cfg.items():
        msg = "creating browse for file://{0} under http @ {1}".format(filepath, url)
        FlaskView.report(msg)
        checks = [
            [len(autoindex_cfg)<2,
             'only support for one static dir now.  sorry :('],
            [ url.startswith('/'),
              'expected url entry would start with a /, got '+url],
            [ ope(filepath),
              "expected path would exist: "+filepath],
            [ isdir(filepath),
              "expected path would be a directory: "+filepath]]
        for check,err in checks: assert check,err
        _install_index(app,filepath,url)

# TODO: just make this standard in corkscrew so other stuff can use it
class MySilk(FlaskView):
    pass

# TODO: ugh this is not used and in fact is not usable.  something about AutoIndex
# is very singleton.. behaviour gets unpredictable when you subclass or instantiate
# multiple objects
class DirIndex(AutoIndex):
    # copied from AutoIndex.__init__ because it didn't support url_root
    # or optional silk instantiation
    def __init__(self, base, browse_root=None, url_root=None, silk=None,
                 add_url_rules=True, **silk_options):

        assert url_root
        self.base = base
        if browse_root:
            self.rootdir = RootDirectory(browse_root, autoindex=self)
        else:
            self.rootdir = None
        if silk is None:
            silk_options['silk_path'] = silk_options.get('silk_path', '/__icons__')
            self.silk = Silk(self.base, **silk_options)
        else:
            self.silk = silk
        self.icon_map = []
        self.converter_map = []
        if add_url_rules:
            @self.base.route(url_root)
            @self.base.route(url_root+'<path:path>')
            def autoindex(path='.'):
                return self.render_autoindex(path)

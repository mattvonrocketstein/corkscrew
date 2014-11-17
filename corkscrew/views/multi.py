""" corkscrew.views.multi
"""
from .lazy import LazyView

class MultiView(LazyView):
    def install_into_app(self, app):
        out=[]
        for View in self.subviews:
            view = View(app=app, settings=self.settings)
            view.install_into_app(app)
            out.append(view)
        return out

"""
"""
from .lazy import LazyView
class FourOhFourView(LazyView):

    template = 'page_not_found.html'

    def __init__(self, *args, **kargs):
        super(FourOhFourView, self).__init__(*args, **kargs)

        @self.app.errorhandler(404)
        def not_found(error):
            return self.render(), 404

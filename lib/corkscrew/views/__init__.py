""" corkscrew.views
"""
from .lazy import LazyView
from .base import FlaskView, View
from .meta import ListViews

from corkscrew.favicon import Favicon
from corkscrew.comet import CometWorker
from corkscrew.proxy import ProxyView
from corkscrew.views.json_edit import JSONEdit
from corkscrew.views.multi import MultiView
from corkscrew.views._404 import FourOhFourView

__all__ = [
    Favicon,
    JSONEdit,
    CometWorker,
    ProxyView,
    FlaskView
    ]

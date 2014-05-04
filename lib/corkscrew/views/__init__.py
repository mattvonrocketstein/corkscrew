""" corkscrew.views
"""
from .lazy import LazyView
from .base import FlaskView, View
from .meta import SettingsView

from corkscrew.favicon import Favicon
from corkscrew.comet import CometWorker
from corkscrew.proxy import ProxyView
from corkscrew.views.json_edit import JSONEdit
from corkscrew.views.multi import MultiView
from corkscrew.views._404 import FourOhFourView

__all__ = [
    View,
    Favicon,
    JSONEdit,
    LazyView,
    ProxyView,
    FlaskView,
    MultiView,
    CometWorker,
    SettingsView,
    FourOhFourView, ]

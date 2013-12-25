""" corkscrew.favicon """

import os
from flask import send_from_directory
from .views import FlaskView, BluePrint


class Favicon(FlaskView):
    """ TODO: change to use settings  """
    url = '/favicon.ico'
    #blueprint = BluePrint('favicon', __name__)
    def main(self):
        return send_from_directory(
            os.path.join(self.app.root_path, 'static'),
            'favicon.ico', mimetype='image/vnd.microsoft.icon')

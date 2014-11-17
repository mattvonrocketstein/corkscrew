""" corkscrew.favicon """

import os
from flask import send_from_directory
from .views import FlaskView


class Favicon(FlaskView):
    """ TODO: change to use settings  """
    url = '/favicon.ico'
    def main(self):
        return send_from_directory(
            os.path.join(self.app.root_path, 'static'),
            'favicon.ico', mimetype='image/vnd.microsoft.icon')

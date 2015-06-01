""" corkscrew.views.robots
"""
import os
from flask import send_from_directory
from corkscrew.views import FlaskView

class RobotsTxt(FlaskView):
    """ TODO: change to use settings  """

    url = '/robots.txt'

    def main(self):
        sdir=os.path.join(self.app.root_path, 'static')
        assert os.path.exists(sdir)
        return send_from_directory(sdir, 'robots.txt')

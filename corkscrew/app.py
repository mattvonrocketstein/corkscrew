""" corkscrew.app

    TODO: better name instead of overloading "app" again..
"""
import json
import addict

class App(addict.Dict):
    def render_json(self):
        return json.dumps(dict(self))

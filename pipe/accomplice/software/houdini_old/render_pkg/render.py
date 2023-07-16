import json
from os import path

class RenderSettings:

    def __init__(self):
        json_path = path.join(path.realpath(path.dirname(__file__)), 'render_settings.json')

        with open(json_path) as f:
            self.render_settings = json.load(f)

    def getAOVs(self):
        return self.render_settings['AOVs']

    def getLayers(self):
        return self.render_settings['layers']

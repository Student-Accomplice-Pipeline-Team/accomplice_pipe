__all__ = ["maya", "houdini", "nuke"]

"""Sets up the configuration for the Pipe"""

import os

film = os.environ.get("FILM")
film_dir = os.environ.get("FILM_DIR")

pipeline_dir = os.environ.get("FILM_PIPELINE_DIR")

icons_dir = os.environ.get("FILM_ICONS_DIR")
pipe_lib = os.environ.get("FILM_PIPE_LIB")
pipe_env = os.environ.get("FILM_PIPE_ENV")
pipe_src = os.environ.get("FILM_PIPE_SRC")
tools_dir = os.environ.get("FILM_PIPE_TOOLS")

anims_dir = os.environ.get("FILM_ANIMATIONS_DIR")
assets_dir = os.environ.get("FILM_ASSETS_DIR")
rigs_dir = os.environ.get("FILM_RIGS_DIR")
shots_dir = os.environ.get("FILM_SHOTS_DIR")
layouts_dir = os.environ.get("FILM_LAYOUTS_DIR")

buildings_dir = os.environ.get("FILM_BUILDINGS_DIR")
characters_dir = os.environ.get("FILM_CHARACTERS_DIR")
props_dir = os.environ.get("FILM_PROPS_DIR")
vehicles_dir = os.environ.get("FILM_VEHICLES_DIR")

# Import the other configs
from . import houdini, maya

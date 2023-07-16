from ..baseclass import EnvSoftwareProxy

from os import path
import os
from typing import Mapping, Optional, Sequence, Union
import subprocess

# See https://www.sidefx.com/docs/houdini/ref/env.html

class HoudiniProxy(EnvSoftwareProxy):
    """A software proxy for Houdini."""

    houdini_pipe_dir = path.realpath(path.dirname(__file__))
    # FIXME: hard coded
    accomplice_path = "/groups/accomplice/pipeline/pipe" # tried just giving it accomplice, but it wanted baseclass since accomplice.py references it
    houdini_env_vars = {
        # 'JOB': '', #TBD where to put this- probably not in an environment variable
        'PYTHONPATH': path.join(houdini_pipe_dir + '/render_pkg') + ":" + accomplice_path, # removed , ";&;"
        # 'HOUDINI_MENU_PATH': path.join(houdini_pipe_dir, 'menu'),
        'HOUDINI_DESK_PATH': path.join(houdini_pipe_dir, 'menu'),
        # 'HOUDINI_TOOLBAR_PATH': path.join(houdini_pipe_dir, 'toolbar'),
        # 'HOUDINI_UI_ICON_PATH': '',
        'HOUDINI_OTLSCAN_PATH': path.join(houdini_pipe_dir, 'hda', ";&"), # digital asset library path?
        # HOUDINI_PATH="${HOUDINI_PATH:+$HOUDINI_PATH:}${houdini_tools};&:${houdini_digital_assets}"
        # 'HOUDINI_PATH': ''                # Custom tools and menus 
        'HOUDINI_NO_ENV_FILE_OVERRIDES': 1, # Prevent user envs from overriding existing values
        'HOUDINI_COREDUMP': 1,              # Dump the core on crash to help debugging
        'HOUDINI_BACKUP_DIR': './.backup',
    }

    def __init__(self,
                 pipe_port: int,
                 command: str = 'houdinifx',
                 args: Optional[Sequence[str]] = ["-foreground"],
                 env_vars: Mapping[str, Optional[str]] = houdini_env_vars,
                 ) -> None:
        super().__init__(pipe_port, command, args, env_vars)
        pass
    

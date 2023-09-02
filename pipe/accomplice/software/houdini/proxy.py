import sys
from os import path
from pathlib import Path
from typing import Mapping, Optional, Sequence, Union

from ..baseclass import HTTPSoftwareProxy

# See https://www.sidefx.com/docs/houdini/ref/env.html

class HoudiniProxy(HTTPSoftwareProxy):
    """A software proxy for Houdini."""

    houdini_pipe_dir = Path(__file__).resolve().parent

    # Configure job path:
    job_dir = houdini_pipe_dir
    while path.basename(job_dir) != 'pipe':
        job_dir = path.dirname(job_dir)

    # Get one more directory above so that, if desired, the JOB variable can be used to access the 'production' folder
    job_dir = path.dirname(job_dir)

    houdini_env_vars = {
        'JOB': job_dir,
        'PYTHONPATH': houdini_pipe_dir,
        'HOUDINI_DESK_PATH': houdini_pipe_dir.joinpath('menu'),         # Custom workspaces
        'HOUDINI_OTLSCAN_PATH': houdini_pipe_dir.joinpath('hda', ";&"), # digital asset library path?
        'HOUDINI_NO_ENV_FILE_OVERRIDES': 1,                             # Prevent user envs from overriding existing values
        'HOUDINI_COREDUMP': 1,                                          # Dump the core on crash to help debugging
        'HOUDINI_PACKAGE_DIR': str(houdini_pipe_dir.joinpath('package')),      # Startup script
        'HOUDINI_BACKUP_DIR': './.backup',                              # Backup directory
        'HOUDINI_MAX_BACKUP_FILES': 20,                                 # Max backup files
        'OCIO': '/opt/pixar/RenderManProServer-25.2/lib/ocio/ACES-1.2/config.ocio',
        'HOUDINI_ASSETGALLERY_DB_FILE': path.join(job_dir, 'production', 'assets', 'assets.db'),   # Asset Gallery
        #'HOUDINI_TOOLBAR_PATH': str(houdini_pipe_dir.joinpath('pipe', 'shelves')),
        #'HOUDINI_SPLASH_MESSAGE': <insert custom message>
        #'HOUDINI_SPLASH_FILE': <insert custom splash>
        #'HOUDINI_ASSETGALLERY_DB_FILE': <insert asset gallery db file>
    }

    def __init__(self,
                 pipe_port: int,
                 command: str = ('/opt/hfs19.5/bin/houdinifx' if sys.platform.startswith('linux') else 'C:\\Program Files\\Side Effects Software\\Houdini 19.5.640\\bin\\houdinifx.exe'),
                 args: Optional[Sequence[str]] = ["-foreground"],
                 env_vars: Mapping[str, Optional[str]] = houdini_env_vars,
                 ) -> None:
        super().__init__(pipe_port, command, args, env_vars)
        pass

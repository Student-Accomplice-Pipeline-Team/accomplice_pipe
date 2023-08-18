"""Define a software proxy for Maya."""

import logging
import sys
from pathlib import Path
from typing import Mapping, Optional, Sequence, Union

from ..baseclass import HTTPSoftwareProxy

log = logging.getLogger(__name__)


class MayaProxy(HTTPSoftwareProxy):
    """A software proxy for Maya."""

    maya_pipe_dir = Path(__file__).resolve().parent
    pipe_dir = maya_pipe_dir.parent.parent

    # TODO: Define colorspace variables to force the correct colorspace
    maya_env_vars = {'PYTHONPATH': maya_pipe_dir,
                     'MAYA_SCRIPT_PATH': str(maya_pipe_dir) + ':' + str(maya_pipe_dir.joinpath('pipe', 'shelves')),
                     #'MAYA_SHELF_PATH': maya_pipe_dir.joinpath('pipe', 'shelves'),
                     'XBMLANGPATH': maya_pipe_dir.joinpath('icons'),
                     'MAYAUSD_EXPORT_MAP1_AS_PRIMARY_UV_SET': 1,
                     'MAYAUSD_IMPORT_PRIMARY_UV_SET_AS_MAP1': 1,
                     'OCIO': None,
                     }

    def __init__(
        self,
        pipe_port: int,
        command: str = ('/usr/local/bin/maya' if sys.platform.startswith('linux') else 'C:\\Program Files\\Autodesk\\Maya2024\\bin\\maya.exe'),
        args: Optional[Sequence[str]] = None,
        env_vars: Mapping[str, Optional[Union[str, int]]] = maya_env_vars,
    ) -> None:
        r"""Initialize MayaProxy objects.

        Keyword arguments: \
        pipe_port -- the port that the pipe is listening to \
        command -- the command to launch Maya \
        args -- the arguments to pass to the command \
        env_vars -- the environment variables to set for Maya
        """
        # Initialize the superclass
        super().__init__(pipe_port, command, args, env_vars)

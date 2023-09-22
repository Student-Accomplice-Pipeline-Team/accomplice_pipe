"""Define a software proxy for Maya."""

import logging
from pathlib import Path
from typing import Mapping, Optional, Sequence, Union

from ..baseclass import HTTPSoftwareProxy

log = logging.getLogger(__name__)


class SubstanceProxy(HTTPSoftwareProxy):
    """A software proxy for Substance Painter."""

    substance_plugin_path = Path(__file__).resolve().parent
    pipe_dir = substance_plugin_path.parent.parent

    # TODO: Define colorspace variables to force the correct colorspace
    substance_env_vars = {'SUBSTANCE_PAINTER_PLUGINS_PATH': substance_plugin_path,
                            'QT_PLUGIN_PATH':           '',}

    def __init__(
        self,
        pipe_port: int,
        command: str = 'D:\\Adobe\\Adobe Substance 3D Painter\\Adobe Substance 3D Painter.exe',
        args: Optional[Sequence[str]] = None,
        env_vars: Mapping[str, Optional[Union[str, int]]] = substance_env_vars,
    ) -> None:
        r"""Initialize SubstanceProxy objects.

        Keyword arguments: \
        pipe_port -- the port that the pipe is listening to \
        command -- the command to launch Maya \
        args -- the arguments to pass to the command \
        env_vars -- the environment variables to set for Maya
        """
        # Initialize the superclass
        super().__init__(pipe_port, command, args, env_vars)

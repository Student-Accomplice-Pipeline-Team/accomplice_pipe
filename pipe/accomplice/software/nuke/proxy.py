from pathlib import Path
import os
from typing import Mapping, Optional, Sequence, Union

from ..baseclass import HTTPSoftwareProxy


class NukeProxy(HTTPSoftwareProxy):
    nuke_pipe_dir = Path(__file__).resolve().parent

    nuke_env_vars = {
        'NUKE_PATH': str(nuke_pipe_dir.joinpath('plugins')),
    }

    launch_args = [
            '-c',
            "QT_SCALE_FACTOR=$NUKE_SCALE_FACTOR /opt/Nuke14.0v5/Nuke14.0 --nukex"
        ]

    is_headless = os.getenv('PIPE_IS_HEADLESS') == '1'

    nuke_script_path = os.getenv('NUKE_SCRIPT_PATH')

    if is_headless:
        launch_args[1] = "QT_SCALE_FACTOR=$NUKE_SCALE_FACTOR /opt/Nuke14.0v5/Nuke14.0 --nukex -t"
    
    if nuke_script_path:
        launch_args[1] = f"QT_SCALE_FACTOR=$NUKE_SCALE_FACTOR /opt/Nuke14.0v5/Nuke14.0 --nukex -t {nuke_script_path}"

    def __init__(
        self,
        pipe_port: int,
        command: str = ('/bin/sh'),
        args: Optional[Sequence[str]] = launch_args,
        env_vars: Mapping[str, Optional[Union[str, int]]] = nuke_env_vars,
    ) -> None:
        r"""Initialize NukeProxy objects.

        Keyword arguments: \
        pipe_port -- the port that the pipe is listening to \
        command -- the command to launch Nuke \
        args -- the arguments to pass to the command \
        env_vars -- the environment variables to set for Nuke
        """
        # Initialize the superclass
        super().__init__(pipe_port, command, args, env_vars)

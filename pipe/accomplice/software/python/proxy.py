from pathlib import Path

from ..baseclass import SoftwareProxy
from typing import Mapping, Optional, Sequence

from ..baseclass import HTTPSoftwareProxy


class PythonProxy(HTTPSoftwareProxy):
    pipe_dir = Path(__file__).resolve().parent
    env_vars = {
        "PYTHONPATH": pipe_dir,
    }

    def __init__(
        self,
        pipe_port: int,
        command: str = "/usr/bin/python3",
        args: Optional[Sequence[str]] = [],
        env_vars: Mapping[str, Optional[str]] = env_vars,
    ) -> None:
        super().__init__(pipe_port, command, args, env_vars)
        pass

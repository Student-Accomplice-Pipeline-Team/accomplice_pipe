"""Base classes for BYU film pipelines."""

from interface import PipeInterface

class SimplePipe(PipeInterface):
    """A simple BYU film pipeline."""

    def __init__(self, *software: str) -> None:
        """Initialize a SimplePipe and launch the given software."""
        # Launch any given software
        for name in software:
            self.launch_software(name)

        # Initialize the superclass
        super().__init__(*software)

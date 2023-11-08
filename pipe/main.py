#!/usr/bin/env python3

r"""Launch BYU film pipelines and software in those pipelines.

When run as a script, parse the pipe and software from the command line
arguments, then run launch(). If pipe is not specified, use the value in
the BYU_FILM_PIPE environment variable.
"""

import os
import logging
from argparse import ArgumentParser
from threading import current_thread

from helper.interface import find_implementation
from interface import PipeInterface

# Variables
pipe_true_root = os.path.realpath(os.path.dirname(__file__))

_pipe_env_var = "BYU_FILM_PIPE"


# Configure logging
log = logging.getLogger(__name__)


def getLevelNamesMapping():
    """Implement the same-named method from the logging module.

    TODO: REPLACE ONCE OUR PYTHON IS >= 3.11
    """
    return logging._nameToLevel.keys()


def launch(pipe: str, *software: str) -> PipeInterface:
    """Launch a BYU film pipeline and software within (if any)."""
    return find_implementation(PipeInterface, pipe)(*software)


# If run as a script, execute launch() with the command-line arguments
# and/or environment variables
if __name__ == "__main__":
    # Parse the arguments
    parser = ArgumentParser(
        description="Launch software in one of BYU's film pipelines."
    )
    parser.add_argument(
        "software",
        nargs="*",
        help="launch the specified software",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        help="log at the specified level. Possible values are %(choices)s (default: %(default)s)",
        choices=getLevelNamesMapping(),
        default=logging.getLevelName(logging.root.level),
        type=str.upper,
        metavar="LEVEL",
    )
    pipe_arg = parser.add_argument(
        "-p",
        "--pipe",
        help=f"use the specified pipe (defaults to ${_pipe_env_var}: %(default)s)",
        default=os.getenv(_pipe_env_var),
    )

    args = parser.parse_args()

    # Set the logging level
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(processName)s(%(process)s) %(threadName)s [%(name)s(%(lineno)s)] [%(levelname)s] %(message)s",
    )

    # Make sure a pipeline has been selected
    if args.pipe is None:
        parser.error(
            f"the following arguments are required: "
            + "/".join(pipe_arg.option_strings + ["$" + _pipe_env_var])
        )

    # Launch the pipeline and software
    pipeline: PipeInterface = launch(args.pipe, *args.software)

    log.info("Exiting")

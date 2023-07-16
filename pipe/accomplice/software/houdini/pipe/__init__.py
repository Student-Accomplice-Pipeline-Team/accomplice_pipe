""""""
import os

from http.client import HTTPConnection
from typing import Optional, Union

from . import shared
from . import asset

from .shared import reload

server = shared.get_proxy()

# _pipe_connection = None


# def _get_connection(host: Optional[str] = None, port: Optional[int] = None):
#     # Make sure the session is initalized
#     global _pipe_connection
#     if _pipe_connection is None:
#         # Get the session destination
#         host = os.getenv(env.vars.SERVER_HOST, 'localhost')
#         port = os.getenv(env.vars.SERVER_PORT)

#         # Initialize the session
#         _pipe_connection = HTTPConnection(host, port)

#     return _pipe_connection

import importlib
import os
import sys
from http.client import HTTPConnection
from inspect import getmembers, isfunction
from typing import Optional, Union
from urllib.parse import urljoin

import maya.cmds as cmds
from pxr import Usd

from . import animation
from . import camera
from . import shelves

from .shared import env, get_proxy, reload
from .shared.object import Asset, Shot

import logging

log = logging.getLogger(__name__)

# Load the pipeline's shelves once the UI has finished loading
print('LOADING SHELVES')
cmds.evalDeferred("pipe.shelves.load()")

# Get a reference to the pipe server
server = get_proxy()

# Create a job to notify the pipe on exit
cmds.scriptJob(
    event=['quitApplication',
            f"pipe.server.exit()"],
    permanent=True,
)

# _proxy_methods = getmembers(_proxy, isfunction)
# print(_proxy_methods)

# _current_module = __import__(__name__)

# for method_def in _proxy_methods:
#     setattr(_current_module, method_def[0], method_def[1])

# from requests import Response, Session

# from .shared import env
# import json

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

# def register():
#     response = _get_connection().request('POST', '/')


# /clients
# 	/
# /users
# /assets
# 	/{asset-id}
# 		/geo
# 		/materials
# 			/textures
# 		/rigs
# /sequences
# 	/{sequence-id}
# 		/shots
# 			/{shot-id}
# 				/anim
# 				/camera
# 				/fx
# 				/layout
# 				/lighting
# 				/render


# /sequences/T/shots/010/anim


# Clients:

# 	Actions:
# 		Register
# 		Find
# 		Watch an asset/shot for changes and do something
# 	Data:
# 		int/str Command port

# 		Id?
# 		Software?

# Assets
# 	Actions:
# 		Check-out
# 		Check-in
# 		Notify update
# 	Data:
# 		int Current version
# 		bool Checkout status
# 		str Checkout user
# 		str Base filepath
# 		bool Final

# Shots
# 	Actions:
# 		Check-out
# 		Check-in
# 		Notify update
# 	Data:
# 		bool Checkout status
# 		str Checkout user
# 		str Base filepath
# 		bool Final


# conn = http.client.HTTPConnection('localhost', server_port)
# conn.request('PUT', '/')
# r1 = conn.getresponse()
# print(r1.status, r1.reason)

# time.sleep(10)
# conn.request('POST', '/', 'exit')
# r2 = conn.getresponse()
# print(r2.status, r2.reason)
# conn.close()

# _pipe_session = None


# class _ServerSession(Session):
#     url_base = None

#     def __init__(
#         self,
#         host: str,
#         port: int,
#     ) -> None:
#         self.url_base = f"http://{host}:{port}"
#         super().__init__()

#     def request(
#             self,
#             method: Union[str, bytes],
#             url: Union[str, bytes],
#             *args,
#             **kwargs
#     ) -> Response:
#         # Join the path to the URL base
#         full_url = urljoin(self.url_base, url)

#         # Send the request
#         return super().request(method, full_url, *args, **kwargs)


# def _get_session(host: Optional[str] = None, port: Optional[int] = None):
#     # Make sure the session is initalized
#     if _pipe_session is None:
#         # Get the session destination
#         host = os.getenv(env.vars.SERVER_HOST, 'localhost')
#         port = os.getenv(env.vars.SERVER_PORT)

#         # Initialize the session
#         _pipe_session = _ServerSession(host, port)

#     return _pipe_session


# def register():
#     response = _get_session().post('/client/register')
#     response.content


# def get_cmdport(client_id: int):
#     _get_session().get(f'/client/cmdport?id={client_id}')
#     pass

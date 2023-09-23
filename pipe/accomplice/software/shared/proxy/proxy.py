import json
import logging
import os
from http import HTTPStatus
from http.client import HTTPConnection, HTTPResponse
from types import SimpleNamespace
from typing import Any, Iterable, Type, Union

from .. import env
from ..exception import ServerError
from ..object import Asset, JsonSerializable, Shot, Character
from .interface import PipeProxyInterface

log = logging.getLogger(__name__)

_proxy = None


def get_proxy(host: str = None, port: int = None):
    """Get the proxy for the pipe."""
    global _proxy
    if _proxy is None:
        _proxy = _PipeProxy(host, port)
    return _proxy


class HTTPMethod:
    """HTTP methods and descriptions.

    TODO: REPLACE ONCE OUR PYTHON IS >= 3.11
    """

    # def __new__(cls, value, description):
    #     obj = str.__new__(cls, value)
    #     obj._value_ = value
    #     obj.description = description
    #     return obj

    # def __repr__(self):
    #     return "<%s.%s>" % (self.__class__.__name__, self._name_)

    CONNECT = 'CONNECT'  # 'Establish a connection to the server.'
    DELETE = 'DELETE'  # 'Remove the target.'
    GET = 'GET'  # 'Retrieve the target.'
    HEAD = 'HEAD'  # 'Same as GET, but only retrieve the status line and header section.'
    OPTIONS = 'OPTIONS'  # 'Describe the communication options for the target.'
    PATCH = 'PATCH'  # 'Apply partial modifications to a target.'
    POST = 'POST'  # 'Perform target-specific processing with the request payload.'
    PUT = 'PUT'  # 'Replace the target with the request payload.'
    TRACE = 'TRACE'  # 'Perform a message loop-back test along the path to the target.'


class _PipeProxy(PipeProxyInterface):
    _conn = None

    def __init__(
        self,
        host: str = None,
        port: int = None,
    ) -> None:
        # Initialize the superclass
        super().__init__()

        # Get the host and port
        if host is None:
            server_host_env = os.getenv(env.vars.SERVER_HOST)
            if server_host_env is not None:
                host = server_host_env
            else:
                host = 'localhost'

        if port is None:
            server_port_env = os.getenv(env.vars.SERVER_PORT)
            if server_port_env is not None:
                port = server_port_env
            else:
                raise AssertionError("No port specified for pipe server")

        log.error(f"Creating connection to {host}:{port}")

        # Create the server connection
        self._conn = HTTPConnection(host, port)

        # Attempt a handshake
        # if not self._do_handshake():
        #    raise ConnectionError("Could not handshake with pipe server")

    def _check_response_status(self, response: HTTPResponse) -> bool:
        # Make sure no errors occurred at the server
        if response.getcode() != HTTPStatus.OK:
            raise ServerError(response.reason)
        return True

    def _parse_response_content(
            self,
            response: HTTPResponse,
            content_class: type = None,
    ) -> Any:
        # Handle content data types appropriately
        content_type = response.getheader('Content-Type')
        content = response.read()

        if content_type == 'application/json':
            # Make sure the requested class is deserializable
            if not issubclass(content_class, JsonSerializable):
                raise ValueError("Response was of type application/json, but "
                                 f"{content_class.__name__} is not "
                                 "deserializable from JSON")

            # Return the deserialized object
            return content_class.from_json(content)
        elif content_type == 'text/plain':
            return content.decode('utf-8')

        # TODO: with latest PR, there are now requests coming back with 'text/html' content type

    def _do_exchange(self, method: str, url: str, body=None):
        # Send the request to the pipe
        self._conn.request(method, url, body)

        # Receive the response and check it for errors
        response = self._conn.getresponse()

        return response

    def _do_handshake(self) -> bool:
        """Handshake with the pipe."""
        response = self._do_exchange(
            HTTPMethod.POST, '/register', bytes(os.getpid()))
        return self._check_response_status(response)

    def _post_data(self, url: str, data_payload: JsonSerializable=None, return_type: type=None):
        """Post data to the pipe."""
        # TODO: you could also add support for a data payload:
        if data_payload is None:
            response = self._do_exchange(HTTPMethod.POST, url)
        else:
            response = self._do_exchange(HTTPMethod.POST, url, data_payload.to_json())
        self._check_response_status(response)
        return self._parse_response_content(response, content_class=return_type)
    
    def _get_data(self, url: str, item_type: type):
        # Request the item from the pipe
        import pdb
        response = self._do_exchange(HTTPMethod.GET, url)
        pdb.set_trace()

        # Parse and return the item
        self._check_response_status(response)
        return self._parse_response_content(response, item_type)
    
    def _generate_query_string(self, endpoint_name:str, params_dict:dict): # TODO: you can update functions to use this
        query_string = '/' + endpoint_name + '?'
        query_string += '&'.join([f'{key}={value}' for key, value in params_dict.items()])
        return query_string

    def get_asset(self, name: str) -> Asset:
        """Get an asset's data from the pipe."""
        sg_path = self._get_data(f'/assets?name={name}'.replace(" ", "+"), Asset).strip()
        split_path = sg_path.split("/")
        file_name = split_path[len(split_path) - 1]
        asset = Asset(file_name)
        asset.path = '/groups/accomplice/pipeline/production/assets' + sg_path
        return asset

    def create_asset(self, asset_name, parent_name='') -> Asset:
        """Create an asset in the pipe."""
        params = {'asset_name': asset_name, 'parent_name': parent_name}
        query_string = self._generate_query_string('create_asset', params)
        return self._post_data(query_string, return_type=Asset)
        
    
    def get_character(self, name: str) -> Character:
        """Get a character's data from the pipe"""
        pipe_path = self._get_data(f'/characters?name={name}', Character).strip()
        character = Character(name)
        character._path = '/groups/accomplice/pipeline/production' + pipe_path
        return character

    def get_character_list(self) -> Iterable[str]:
        """Get a list of all characters from the pipe."""
        return self._get_data('/characters?list=name', str).split(',')

    def get_asset_list(self) -> Iterable[str]:
        """Get a list of all assets from the pipe."""
        return self._get_data('/assets?list=name', str).split(',')

    def get_assets(self, *names) -> Iterable[Asset]:
        """Get asset data from the pipe. NOT FULLY IMPLEMENTED."""
        # Construct the URL
        url = '/assets'
        if names:
            url += '?' + ','.join(names)
        else:
            print("WARNING: NOT FULLY IMPLEMENTED")

        return self._get_data(url, Iterable[Asset])

    def get_shot(self, name: str) -> Shot:
        """Get a shot's data from the pipe."""
        shot = Shot(name)
        shot.path = f'/groups/accomplice/pipeline/production/sequences/{name[0]}/shots/{name[2:]}'
        return shot

    def get_shot_list(self) -> Iterable[str]:
        """Get a list of all shots from the pipe."""
        return self._get_data('/shots?list=name', str).split(',')
    
    def shot_update(self, name: str):
        pass

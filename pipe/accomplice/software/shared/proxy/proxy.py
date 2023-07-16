import json
import logging
import os
from http import HTTPStatus
from http.client import HTTPConnection, HTTPResponse
from types import SimpleNamespace
from typing import Any, Iterable, Type, Union

from .. import env
from ..exception import ServerError
from ..object import Asset, JsonSerializable, Shot
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

    def _get_data(self, url: str, item_type: type):
        # Request the item from the pipe
        response = self._do_exchange(HTTPMethod.GET, url)

        # Parse and return the item
        self._check_response_status(response)
        return self._parse_response_content(response, item_type)

    def get_asset_list(self) -> Iterable[str]:
        """Get a list of all assets from the pipe."""
        return self._get_data('/assets?list=name', str).split(',')

    def get_asset(self, name: str) -> Asset:
        """Get an asset's data from the pipe."""
        asset = Asset(name)
        asset.path = '/groups/accomplice/pipeline/production/asset' + self._get_data(f'/assets?name={name}', Asset).strip()
        return asset
        #return self._get_data(f'/assets?name={name}', Asset)

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
        return self._get_data(f'/shots?name={name}', Shot)
    
    def shot_update(self, name: str):
        pass

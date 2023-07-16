"""Base classes for interacting with software via a proxy."""

import logging
import os
import subprocess
from functools import partial
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler
from socket import AF_INET, SOCK_STREAM
from socket import socket as Socket
from typing import Mapping, Optional, Sequence, Union

from ..server import HTTPServerThread
from .interface import SoftwareProxyInterface
from .shared import env

log = logging.getLogger(__name__)


class SoftwareProxy(SoftwareProxyInterface):
    """A proxy for software."""

    command = None
    args = None
    pipe_port = None

    processes = []

    def __init__(
            self,
            pipe_port: int,
            command: str,
            args: Optional[Sequence[str]] = None,
    ) -> None:
        """Initialize SoftwareProxy objects.

        Arguments:
        - pipe_port -- the port on which the pipe server is listening

        Keyword arguments:
        - command -- the command to launch the software
        - args -- the arguments to pass to the command
        """
        # Initialize args with a default value if missing
        if args is None:
            args = []

        # Initialize instance variables
        self.pipe_port = pipe_port
        self.command = command
        self.args = args

    def launch(
        self,
        command: Optional[str] = None,
        args: Optional[Sequence[str]] = None,
    ) -> None:
        r"""Launch the software with the specified arguments.

        Passing in optional parameters will override their default
        values.

        Overrides SoftwareProxyInterface.launch().
        """
        # Use default values if none are provided
        if command is None:
            command = self.command
        if args is None:
            args = self.args

        # Run the command with the arguments
        log.info("Launching the software")
        self.processes.append(
            subprocess.Popen([command] + args)
            # stdout=subprocess.DEVNULL,
            # stderr=subprocess.DEVNULL)
        )


class EnvSoftwareProxy(SoftwareProxy):
    """A proxy for software that need pre-built environments."""

    env_vars = None

    def __init__(
            self,
            pipe_port: int,
            command: str,
            args: Optional[Sequence[str]] = None,
            env_vars: Mapping[str, Optional[Union[str, int]]] = None
    ) -> None:
        r"""Initialize EnvSoftwareProxy objects.

        Keyword arguments:
         - command -- the command to launch the software
         - args -- the arguments to pass to the command
         - env_vars -- the environment variables to set for the software
        """
        # Initialize the superclass
        super().__init__(pipe_port, command, args)

        # Initialize values for any missing optional variables
        if env_vars is None:
            env_vars = {}

        # Initialize instance variables
        self.env_vars = env_vars

    def _env_hook(self) -> None:
        """Customize the software environment beyond env variables.

        Does nothing by default.
        """
        pass

    def _set_env_vars(
        self,
        env_vars: Optional[Mapping[str, Optional[Union[str, int]]]]
    ) -> None:
        """(Un)Set environment variables to their associated values.

        All values will be converted to strings. If a value is None,
        that environment variable will be unset.
        """
        # Use default environment variables if none are provided
        if env_vars is None:
            env_vars = self.env_vars

        # (Un)Set the environment variables
        for key, val in env_vars.items():
            if val is None:
                os.unsetenv(key)
            else:
                os.environ[key] = str(val)

    def _build_env(
        self,
        env_vars: Optional[Mapping[str, Optional[Union[str, int]]]],
    ) -> None:
        r"""Build the environment for the software.

        The environment setup includes setting environment variables \
        and executing the environment hook (if any).

        Passing in optional parameters will override their default \
        values.
        """
        log.info("Building the software environment")

        # Set the environment variables
        self._set_env_vars(env_vars)

        # Run the environment hook
        self._env_hook()

    def launch(
        self,
        command: Optional[str] = None,
        args: Optional[Sequence[str]] = None,
        env_vars: Optional[Mapping[str, Optional[Union[str, int]]]] = None,
    ) -> None:
        r"""Build the environment for and launch the software.

        Passing in optional parameters will override their default
        values.

        Overrides SoftwareProxy.launch().
        """
        # Build the software environment
        self._build_env(env_vars)

        # Launch the software
        super().launch(command, args)


class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    forward_port = None

    def __init__(self, forward_port: int, *args) -> None:
        # Set instance variables
        self.forward_port = forward_port

        # Initialize the superclass and resolve the request
        super().__init__(*args)

    def _forward_request(self, method: str, content: bytes):
        log.info(f"Forwarding {method} request")

        # Forward the request to the pipe server
        conn = HTTPConnection('localhost', self.forward_port)
        conn.request(method, self.path, content, self.headers)

        # Wait for a response
        response = conn.getresponse()

        # Get the response content
        #response_content_len = int(
        #    response.headers.get('Content-Length', failobj=0))
        response_content = response.read()

        log.info(f"Received response with {response_content.decode('utf-8')}")

        # Forward the response to the client
        self.send_response(response.status)
        for keyword, value in response.headers.items():
            self.send_header(keyword, value)
        self.end_headers()
        self.wfile.write(response_content)

    def _handle_request(self, method: str, content: bytes):
        log.info(f"Handling {method} request")

    def _resolve_request(self, method: str):
        log.info(f"Received {method} request from {self.client_address}")

        # Get the request content
        content_len = int(
            self.headers.get('Content-Length', failobj=0)
        )
        content = self.rfile.read(content_len)

        # Handle or forward the request
        if self.path.split('/')[0] == 'client':
            # TODO: somehow register a client???
            pass
        else:
            self._forward_request(method, content)

    def do_GET(self):
        self._resolve_request('GET')

    def do_POST(self):
        self._resolve_request('POST')

    def do_PUT(self):
        self._resolve_request('PUT')


class HTTPSoftwareProxy(EnvSoftwareProxy):
    _port = None
    httpd = None
    instances = []

    @property
    def port(self):
        if self.httpd is None:
            return self._port
        else:
            return self.httpd.port

    @port.setter
    def port(self, value):
        if self.httpd is None:
            self._port = value
        else:
            raise Exception("A problem has occurred")

    def __init__(
            self,
            pipe_port: int,
            command: str,
            args: Optional[Sequence[str]] = None,
            env_vars: Mapping[str, Optional[Union[str, int]]] = None,
            bind_port: Optional[int] = None,
    ) -> None:
        # Initialize the superclass
        super().__init__(pipe_port, command, args, env_vars)

        # Store the port number if present
        self.port = bind_port if bind_port is not None else 0

    def launch(
        self,
        command: Optional[str] = None,
        args: Optional[Sequence[str]] = None,
        env_vars: Optional[Mapping[str, Optional[Union[str, int]]]] = None,
    ) -> None:
        # Ensure the proxy server is running
        if self.httpd is None:
            log.info("Initializing the server")

            # Initialize the proxy server
            address = ('localhost', self.port)
            request_handler = partial(ProxyHTTPRequestHandler, self.pipe_port)

            self.httpd = HTTPServerThread(address, request_handler)

            # Start the proxy server
            log.info("Starting the proxy server")
            self.httpd.start()

        # Use the default environment variables if necessary
        if env_vars is None:
            env_vars = self.env_vars.copy()

        # TODO: Warning if the server port var is overridden
        if env.vars.SERVER_PORT in env_vars:
            pass

        # Add the server port to the environment variables
        env_vars.update({env.vars.SERVER_PORT: self.port})

        # Add a command port to the environment variables if necessary
        # if self.CMD_PORT_VAR not in env_vars:
        #     # Find a free port for the software's command port
        #     cmd_port = self._find_free_port()
        #     # self._ports.append(cmd_port)

        #     # Set the environment variable
        #     env_vars.update({self.CMD_PORT_VAR: cmd_port})

        # Launch the software
        super().launch(command, args, env_vars)

    def exit(self):
        # Shut down the server
        log.info('Shutting down the proxy server')
        self.httpd.shutdown()


# NOTE [MA]: Here for reference, will delete once I'm sure it's no longer needed
# ----------------------
# class PipeEnvSoftwareProxy(EnvSoftwareProxy):
#     """A proxy for software that need pre-built environments."""

#     env_vars = None

#     def __init__(
#             self,
#             pipe_port: int,
#             command: str,
#             args: Optional[Sequence[str]] = None,
#             env_vars: Mapping[str, Optional[Union[str, int]]] = None
#     ) -> None:
#         # Initialize values for any missing optional variables
#         if env_vars is None:
#             env_vars = {}

#         # Initialize the superclass
#         super().__init__(pipe_port, command, args)


#         # Initialize instance variables
#         self.env_vars = env_vars

# class CmdPortSoftwareProxy(EnvSoftwareProxy, Thread):
#     """A proxy for software that opens a command port to communicate."""

#     SERVER_PORT_VAR = 'SERVER_PORT'
#     CMD_PORT_VAR = 'COMMAND_PORT'

#     _CHUNK_SIZE = 1024

#     port: Optional[int] = None

#     _server_sock: Socket = None

#     _inputs = []
#     _outputs = []
#     _msg_queues: Mapping[Socket, Queue] = {}

#     def __init__(
#             self,
#             pipe_port: int,
#             command: str,
#             args: Optional[Sequence[str]] = None,
#             env_vars: Mapping[str, Optional[Union[str, int]]] = None,
#             port: Optional[int] = None,
#     ) -> None:
#         # Initialize the superclass
#         super().__init__(pipe_port, command, args, env_vars)

#         # Store the server port number if present
#         self.port = port if port is not None else 0

#     def exit(self) -> None:
#         log.info("Closing incoming connections")

#         # Close all input sockets
#         for sock in self._inputs:
#             self._close_connection(sock)

#     def _find_free_port(self) -> int:
#         # Bind a socket to an open port
#         sock = Socket()
#         sock.bind(('localhost', 0))

#         # Get the socket's port number
#         port = sock.getsockname()[1]

#         # Close the socket
#         sock.close()

#         # Return the port number
#         return port

#     def _process_data(self, client_sock: Socket, data: bytes) -> None:
#         """Process the data received from the given socket."""
#         # Decode the data as a string
#         try:
#             data = data.decode()
#             log.debug(
#                 f"Data from port {client_sock.getsockname()[1]}: '{data}'")
#         except UnicodeDecodeError:
#             log.error("Could not decode data", exc_info=True)

#         if data == 'exit':
#             self.exit()

#     def _create_socket(self, port: Optional[int] = None) -> Socket:
#         # Create a nonblocking TCP/IP socket
#         sock = Socket(AF_INET, SOCK_STREAM)
#         sock.setblocking(0)

#         # Bind to a port
#         sock.bind(('localhost', port if port is not None else self.port))

#         # Set to listen for incoming connections
#         sock.listen()

#         # Return the socket
#         return sock

#     def _accept_connection(self) -> None:
#         # Accept the connection
#         client_sock, _ = self._server_sock.accept()
#         client_sock.setblocking(0)

#         # Add the socket to input polling
#         self._inputs.append(client_sock)

#         # Create a queue for the connection
#         self._msg_queues[client_sock] = Queue()

#         log.debug(
#             f"Established connection on port {client_sock.getsockname()[1]}")

#     def _close_connection(self, sock: Socket) -> None:
#         # Remove the socket from polling
#         self._inputs.remove(sock)
#         if sock in self._outputs:
#             self._outputs.remove(sock)

#         # Close the connection
#         sock.close()

#         # Delete the connection's queue, if present
#         if sock in self._msg_queues.keys():
#             del self._msg_queues[sock]

#     def _send_msg(self, sock: Socket, msg):
#         # Prefix the message with a four-byte big-endian length
#         msg = struct.pack('>I', len(msg)) + msg

#         # Send the message
#         sock.sendall(msg)

#     def _recv_msg(self, sock: Socket):
#         # Read the message length
#         raw_msglen = self._recv_bytes(sock, 4)

#         # Check if EOF was hit
#         if not raw_msglen:
#             return None

#         # Unpack the message length
#         msg_len = struct.unpack('>I', raw_msglen)[0]

#         # Read the message data
#         return self._recv_bytes(sock, msg_len)

#     def _recv_bytes(self, sock: Socket, num_bytes: int):
#         # Read the number of bytes from the socket
#         data = bytearray()
#         while len(data) < num_bytes:
#             # Read a packet from the socket
#             packet = sock.recv(num_bytes - len(data))

#             # Check if EOF was hit
#             if not packet:
#                 return None

#             # Add the packet to the data buffer
#             data.extend(packet)
#         return data

#     def _start(self) -> None:
#         # Start the server if necessary
#         if self._server_sock is None:
#             log.info("Starting the proxy server")
#             # Create the server socket
#             self._server_sock = self._create_socket(self.port)

#             # Update the server port number
#             self.port = self._server_sock.getsockname()[1]

#             # Add the server socket to input polling
#             self._inputs.append(self._server_sock)

#     def run(self) -> None:
#         """Start the server and execute the main polling loop."""
#         # Poll I/O until there's no more input
#         while self._inputs:
#             # Wait for a socket to be ready for processing
#             readable, writable, exceptional = select(
#                 self._inputs, self._outputs, self._msg_queues)

#             # Handle input sockets
#             for sock in readable:
#                 # Check if the socket is the server or a client socket
#                 if sock is self._server_sock:
#                     # Accept incoming connections
#                     log.info(f"Detected incoming connection")
#                     self._accept_connection()
#                 else:
#                     # Check if the socket has data or was disconnected
#                     data = self._recv_msg(sock)
#                     if data:
#                         log.info("Received data from port " +
#                                  f"{sock.getsockname()[1]}")
#                         self._process_data(sock, data)
#                     else:
#                         log.info("Connection on port " +
#                                  f"{sock.getsockname()[1]} was disconnected")
#                         self._close_connection(sock)

#             # Handle output sockets
#             for sock in writable:
#                 try:
#                     # Send the socket's next waiting message
#                     msg = self._msg_queues[sock].get_nowait()
#                     log.info(
#                         f"Sending message on port {sock.getsockname()[1]}")
#                     sock.send(msg)
#                 except queue.Empty:
#                     # Remove the socket from output polling
#                     self._outputs.remove(sock)

#             # Close errored sockets
#             for sock in exceptional:
#                 log.warning(
#                     f"Exception occurred on port {sock.getsockname()[1]}")
#                 self._close_connection(sock)

#     def launch(
#         self,
#         command: Optional[str] = None,
#         args: Optional[Sequence[str]] = None,
#         env_vars: Optional[Mapping[str, Optional[Union[str, int]]]] = None,
#     ) -> None:
#         f"""Build the environment for and launch the software.

#         When launching software, stores the command port and server port
#         numbers in the CmdPortSoftwareProxy.CMD_PORT_VAR and
#         CmdPortSoftwareProxy.SERVER_PORT_VAR environment variables,
#         respectively.
#         """

#         # Use the default environment variables if necessary
#         if env_vars is None:
#             env_vars = self.env_vars.copy()

#         # TODO: Warning if the server port var is overridden
#         if self.SERVER_PORT_VAR in env_vars:
#             pass

#         # Add the server port to the environment variables
#         env_vars.update({self.SERVER_PORT_VAR: self.port})

#         # Add a command port to the environment variables if necessary
#         if self.CMD_PORT_VAR not in env_vars:
#             # Find a free port for the software's command port
#             cmd_port = self._find_free_port()
#             # self._ports.append(cmd_port)

#             # Set the environment variable
#             env_vars.update({self.CMD_PORT_VAR: cmd_port})

#         # Launch the software
#         super().launch(command, args, env_vars)

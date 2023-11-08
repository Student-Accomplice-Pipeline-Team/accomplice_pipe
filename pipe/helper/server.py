import queue
from abc import ABCMeta, abstractmethod
from queue import Queue
from select import select
from socket import AF_INET, SOCK_STREAM
from socket import socket as Socket
from typing import Optional

from helper import interface


class Server(metaclass=ABCMeta):
    """A server."""

    _CHUNK_SIZE = 1024

    _port: Optional[int] = None
    _server_sock: Socket = None

    _inputs = []
    _outputs = []
    _msg_queues = {}

    @classmethod
    def __subclasshook__(cls, subclass) -> bool:
        """Determine if the given class is a subclass."""
        return interface.check_methods(cls, subclass)

    def __init__(self, port: Optional[int] = None):
        # Store the server's port number if present
        self._port = port if port is not None else 0

    @abstractmethod
    def _process_data(self, client_sock: Socket, data: bytes) -> None:
        """Process the data received from the given socket."""
        raise NotImplementedError

    def _create_socket(self, port: Optional[int] = None) -> Socket:
        # Create a nonblocking TCP/IP socket
        sock = Socket(AF_INET, SOCK_STREAM)
        sock.setblocking(0)

        # Bind to a port
        sock.bind(("localhost", port if port is not None else self._port))

        # Set to listen for incoming connections
        sock.listen()

        # Return the socket
        return sock

    def _accept_connection(self) -> None:
        # Accept the connection
        client_sock, _ = self._server_sock.accept()
        client_sock.setblocking(0)

        # Add the socket to input polling
        self._inputs.append(client_sock)

        # Create a queue for the connection
        self._msg_queues[client_sock] = Queue()

    def _close_connection(self, sock: Socket) -> None:
        # Remove the socket from polling
        self._inputs.remove(sock)
        if sock in self._outputs:
            self._outputs.remove(sock)

        # Close the connection
        sock.close()

        # Delete the connection's queue
        del self._msg_queues[sock]

    def _recvall(self, sock: Socket) -> Optional[bytes]:
        # Get the first chunk of data
        chunk = sock.recv(self._CHUNK_SIZE)
        data = chunk

        # Get any remaining data
        while len(chunk) == self._CHUNK_SIZE:
            chunk = sock.recv(self._CHUNK_SIZE)
            data += chunk

        return data

    def run(self) -> None:
        # Create the server socket and add it to input polling
        self._server_sock = self._create_socket()
        self._port = self._server_sock.getsockname()[1]
        self._inputs.append(self._server_sock)

        while self._inputs:
            # Wait for a socket to be ready for processing
            readable, writable, exceptional = select(
                self._inputs, self._outputs, self._msg_queues
            )

            # Handle input sockets
            for sock in readable:
                # Check if the socket is the server or a client socket
                if sock is self._server_sock:
                    self._accept_connection()
                else:
                    # Check if the socket has data or is disconnected
                    data = self._recvall(sock)
                    if data:
                        self.process_data(data)
                    else:
                        self._close_connection(sock)

            # Handle output sockets
            for sock in writable:
                try:
                    # Get and send the next waiting message
                    msg = self._msg_queues[sock].get_nowait()
                    sock.send(msg)
                except queue.Empty:
                    # Remove the socket from output polling
                    self._outputs.remove(sock)

            # Handle errored sockets
            for sock in exceptional:
                self._close_connection(sock)

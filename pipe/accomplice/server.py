"""Server helper classes."""

import atexit
import logging
from http.client import HTTPConnection
from http.server import HTTPServer
from socketserver import BaseRequestHandler
from threading import Thread
from typing import Optional, Tuple, Union

log = logging.getLogger(__name__)


class HTTPServerThread(Thread):
    """A thread that runs an HTTP server."""

    _httpd = None
    _thread = None

    @property
    def port(self) -> int:
        """The port the HTTP server is running on."""
        if self._httpd is None:
            return 0
        else:
            return self._httpd.server_port

    def __init__(
        self,
        server_address: Tuple[Union[str, bytes, bytearray], int],
        RequestHandlerClass: BaseRequestHandler,
        bind_and_activate: bool = True,
        thread_name: Optional[str] = None
    ) -> None:
        """Initialize an HTTPServerThread object."""
        super().__init__(name=thread_name)

        # Initialize the server
        self._httpd = HTTPServer(
            server_address, RequestHandlerClass, bind_and_activate)

    def run(self) -> None:
        """Run the HTTP server."""
        try:
            log.info("Staring httpd...")
            self._httpd.serve_forever()
        except KeyboardInterrupt:
            pass

        log.info("Closing httpd...")
        self._httpd.server_close()

    def shutdown(self):
        """Shut down the server and join, blocking until complete."""
        self._httpd.shutdown()
        self.join()

from typing import Union
from urllib.parse import urljoin

#from requests import Response, Session
import os
import env

# _session = None

# def get_session():
#     if _conn is None:
#         host = os.getenv(env.vars.SERVER_HOST)
#         port = os.getenv(env.vars.SERVER_PORT)
#         _conn = ServerSession(host, port)
#     return _conn

# class ServerSession(Session):
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
#         full_url = urljoin(self.url_base, url)
#         return super().request(method, full_url, *args, **kwargs)


# class ServerSession(Session):
#     url_base = None

#     def __init__(self, url_base: Union[str, bytes] = None):
#         super().__init__()
#         self.url_base = url_base

#     def request(
#             self,
#             method: Union[str, bytes],
#             url: Union[str, bytes],
#             *args,
#             **kwargs
#     ) -> Response:
#         full_url = urljoin(self.url_base, url)
#         return super().request(method, full_url, *args, **kwargs)

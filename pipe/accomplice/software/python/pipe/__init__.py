import os

from http.client import HTTPConnection
from typing import Optional, Union

from . import shared
# from . import asset

from .shared import reload

server = shared.get_proxy()

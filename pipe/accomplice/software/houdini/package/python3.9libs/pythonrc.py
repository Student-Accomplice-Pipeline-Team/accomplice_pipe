"""Initialize the Houdini pipeline environment on startup."""
import pipe
import logging
import os
from pathlib import *
import hou

log = logging.getLogger(__name__)

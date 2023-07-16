"""Nuke proxy"""

import sys

from .. import SoftwareProxyInterface
from .proxy import NukeProxy

# Replace this module with a NukeProxy instance
sys.modules[__name__]: SoftwareProxyInterface = NukeProxy()

import importlib
import logging
import sys

from . import env
from .proxy import get_proxy
from .object import Asset
from . import versions
from . import permissions
log = logging.getLogger(__name__)


def reload():
    """Reload all pipe python modules."""
    pipe_modules = [module for name, module in sys.modules.items()
                    if name.startswith('pipe')]

    for module in pipe_modules:
        log.info(f"Reloading {module.__name__}")
        importlib.reload(module)

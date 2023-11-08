"""Provide classes for interaction with various software.

TODO: To define a new software proxy, do blah blah blah...
"""

__all__ = ["houdini", "maya", "nuke"]

from helper.interface import find_implementation

from .interface import SoftwareProxyInterface


def create_proxy(name: str, pipe_port: int) -> SoftwareProxyInterface:
    """Create and return a proxy for the specified software."""
    return find_implementation(SoftwareProxyInterface, "." + name, __package__)(
        pipe_port
    )

"""Interfaces for interacting with software through proxies."""

from abc import ABCMeta, abstractmethod

from helper import interface


class SoftwareProxyInterface(metaclass=ABCMeta):
    """An interface for software proxies."""

    @classmethod
    def __subclasshook__(cls, subclass) -> bool:
        """Determine if the given class is a subclass."""
        return interface.check_methods(cls, subclass)

    @abstractmethod
    def __init__(self, pipe_port: int):
        """Initialize the SoftwareProxy."""
        raise NotImplementedError

    @abstractmethod
    def launch(self) -> None:
        """Launch the software."""
        raise NotImplementedError


class USDSoftwareProxyInterface(SoftwareProxyInterface):
    """An interface for proxies of software that support USDs."""

    @abstractmethod
    def import_usd(self, path: str) -> None:
        """Import a USD."""
        raise NotImplementedError

    @abstractmethod
    def export_usd(self, path: str) -> None:
        """Export a USD."""
        raise NotImplementedError

"""Interfaces for interacting with the database"""

from abc import ABCMeta, abstractmethod

from helper import interface

from typing import Iterable, Set, Sequence

from shared.object import Asset

class DatabaseInterface(metaclass=ABCMeta):
    """Interface for database interaction"""

    @classmethod
    def __subclasshook__(cls, subclass: type) -> bool:
        """Determine if the given class is a subclass"""
        return interface.check_methods(cls, subclass)

    @abstractmethod
    def __init__(self) -> None:
        """Initialize the Database"""
        raise NotImplementedError
    
    @abstractmethod
    def get_asset(self, name: str) -> Asset:
        """Get an Asset object"""
        raise NotImplementedError

    @abstractmethod
    def get_assets(self, names: Iterable[str]) -> Set[Asset]:
        """Get multiple Asset objects"""
        raise NotImplementedError

    @abstractmethod
    def get_asset_list(self) -> Sequence[str]:
        """Get a list of Asset ids"""
        raise NotImplementedError

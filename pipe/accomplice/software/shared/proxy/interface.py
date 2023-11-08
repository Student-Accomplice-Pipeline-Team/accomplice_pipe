from abc import ABCMeta, abstractmethod

from ..helper.interface import check_methods

from ..object import Asset, Shot, Character


class PipeProxyInterface(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass) -> bool:
        """Determine if the given class is a subclass."""
        return check_methods(cls, subclass)

    @abstractmethod
    def get_asset(self, name: str) -> Asset:
        """TODO: DOCSTRING.

        Pass 'all' to select all assets.
        """
        pass

    @abstractmethod
    def get_shot(self, name: str) -> Shot:
        pass

    @abstractmethod
    def get_character(self, name: str) -> Character:
        pass

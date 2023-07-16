"""Define an interface for BYU film pipelines."""

from abc import ABCMeta, abstractmethod

from helper.interface import check_methods


class PipeInterface(metaclass=ABCMeta):
    """An interface for BYU's film pipelines."""

    @classmethod
    def __subclasshook__(cls, subclass):
        """Ensure that subclasses contain implementations of all methods."""
        return check_methods(cls, subclass)
    
    def __init__(self, *software: str) -> None:
        """Initialize the pipe and launch the software, if any."""
        pass

    @abstractmethod
    def launch_software(self, name: str) -> None:
        """Launch the film's cut of the software."""
        raise NotImplementedError

    # @abstractmethod
    # def publish_geo(self, asset_name: str, is_hero=False):
    #     """Publish the selected geo from the current software."""
    #     raise NotImplementedError

    # @abstractmethod
    # def publish_material(self, asset_name: str, is_hero=False):
    #     """Publish the selected material from the current software."""
    #     raise NotImplementedError

    # @abstractmethod
    # def publish_rig(self, asset_name: str, is_hero=False):
    #     """Publish the selected rig from the current software."""
    #     raise NotImplementedError

    # @abstractmethod
    # def publish_asset(self, asset_name: str, is_hero=False):
    #     """Publish the selected asset from the current software."""
    #     raise NotImplementedError

    # @abstractmethod
    # # Multiple animations per shot?
    # def publish_anim(self, shot_name: str):
    #     """Publish the selected animation from the current software."""
    #     raise NotImplementedError

    # @abstractmethod
    # def publish_camera(self, shot_name: str):
    #     """Publish the selected camera from the current software."""
    #     raise NotImplementedError

    # @abstractmethod
    # # Multiple fx per shot?
    # def publish_fx(self, shot_name: str):
    #     """Publish the selected fx from the current software"""
    #     raise NotImplementedError

    # @abstractmethod
    # def publish_layout(self, shot_name: str):
    #     """Publish the selected layout from the current software"""
    #     raise NotImplementedError

    # @abstractmethod
    # def publish_lighting(self, shot_name: str):
    #     """Publish the selected lights from the current software"""
    #     raise NotImplementedError

    # @abstractmethod
    # def checkout_geo(self, asset_name: str, is_hero=False):
    #     raise NotImplementedError

    # @abstractmethod
    # def checkout_material(self, asset_name: str, is_hero=False):
    #     raise NotImplementedError

    # @abstractmethod
    # def checkout_rig(self, asset_name: str, is_hero=False):
    #     raise NotImplementedError

    # @abstractmethod
    # def checkout_asset(self, asset_name: str, is_hero=False):
    #     raise NotImplementedError

    # @abstractmethod
    # # Multiple animations per shot?
    # def checkout_anim(self, shot_name: str):
    #     raise NotImplementedError

    # @abstractmethod
    # def checkout_camera(self, shot_name: str):
    #     raise NotImplementedError

    # @abstractmethod
    # # Multiple fx per shot?
    # def checkout_fx(self, shot_name: str):
    #     raise NotImplementedError

    # @abstractmethod
    # def checkout_layout(self, shot_name: str):
    #     raise NotImplementedError

    # @abstractmethod
    # def checkout_lighting(self, shot_name: str):
    #     raise NotImplementedError

    # @abstractmethod
    # def reference_rig(self, asset_type: str, asset_name: str):
    #     raise NotImplementedError

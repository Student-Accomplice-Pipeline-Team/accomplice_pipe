"""A collection of helper methods for interfaces."""

import importlib
import importlib.util
from inspect import getmembers, isabstract, isclass, isfunction
from typing import Optional


def check_methods(cls: type, subclass: type) -> bool:
    """Check if a class implements another class's methods."""
    # Get the names of the class's methods
    methods: list = [member[0] for member in getmembers(cls, isfunction)]

    # Get the subclass's method resolution order (MRO)
    mro = subclass.__mro__

    # Check if the subclass's MRO contains every method
    for method in methods:
        for entry in mro:
            if method in entry.__dict__:
                if entry.__dict__[method] is None:
                    return NotImplemented
                break
        else:
            return NotImplemented
    return True


def find_implementation(cls: type, module: str, package: Optional[str] = None) -> type:
    """Find an implementation of the class in the specified module."""
    # Check if the specified module exists
    if importlib.util.find_spec(module, package):
        # Import the module
        imported_module = importlib.import_module(module, package)

        # Check if the submodule contains an implementation of the class
        classes = getmembers(
            imported_module,
            lambda obj: isclass(obj) and not isabstract(obj) and issubclass(obj, cls),
        )

        # Check if more or less than one implementation was found
        if len(classes) < 1:
            raise AssertionError(
                f"module '{module}' does not contain an "
                f"implementation of class '{cls.__name__}'"
            )
        elif len(classes) > 1:
            raise AssertionError(
                f"module '{module}' contains multiple "
                f"implementations of class '{cls.__name__}'"
            )

        # Return the implementing class
        return classes[0][1]

    else:
        raise ValueError(f"could not find module '{module}'")

"""Base classes for interacting with the database"""

from .interface import DatabaseInterface


class Database(DatabaseInterface):
    """Database"""

    def __init__(self):
        pass
